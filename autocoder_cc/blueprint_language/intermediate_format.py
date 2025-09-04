#!/usr/bin/env python3
"""
Autocoder v4.3 Intermediate Blueprint Format
A simplified, well-specified format for defining systems that can be translated to full blueprints
"""
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, field_validator
import re


class IntermediatePort(BaseModel):
    """Simplified port definition"""
    name: str = Field(..., pattern="^[a-z][a-z0-9_]*$", description="Port name in snake_case")
    schema_type: Literal["object", "array", "string", "number", "integer", "boolean"] = Field(..., description="Basic schema type")
    description: Optional[str] = Field(None, description="Port description")
    required: bool = Field(True, description="Whether this port is required")


class IntermediateComponent(BaseModel):
    """Simplified component definition"""
    name: str = Field(..., pattern="^[a-z][a-z0-9_]*$", description="Component name in snake_case")
    type: Literal["Source", "Transformer", "Accumulator", "Store", "Controller", "Sink", "StreamProcessor", "Model", "APIEndpoint", "Router"] = Field(..., description="Component type")
    description: Optional[str] = Field(None, description="Component description")
    inputs: List[IntermediatePort] = Field(default_factory=list, description="Input ports")
    outputs: List[IntermediatePort] = Field(default_factory=list, description="Output ports")
    
    # Simplified configuration - only the most common settings
    config: Dict[str, Any] = Field(default_factory=dict, description="Component-specific configuration")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not re.match(r'^[a-z][a-z0-9_]*$', v):
            raise ValueError(f"Component name '{v}' must be snake_case")
        return v
    
    model_config = {"extra": "forbid"}  # Prevent unexpected fields


class IntermediateBinding(BaseModel):
    """Simplified binding definition"""
    from_component: str = Field(..., description="Source component name")
    from_port: str = Field(..., description="Source port name")
    to_component: str = Field(..., description="Target component name")
    to_port: str = Field(..., description="Target port name")
    
    @field_validator('from_component', 'from_port', 'to_component', 'to_port')
    @classmethod
    def validate_names(cls, v):
        if not re.match(r'^[a-z][a-z0-9_]*$', v):
            raise ValueError(f"Name '{v}' must be snake_case")
        return v
    
    model_config = {"extra": "forbid"}


class IntermediateSystem(BaseModel):
    """Complete intermediate system definition"""
    name: str = Field(..., pattern="^[a-z][a-z0-9_]*$", description="System name in snake_case")
    description: str = Field(..., description="System description")
    version: str = Field("1.0.0", pattern="^\\d+\\.\\d+\\.\\d+$", description="System version (semver)")
    
    components: List[IntermediateComponent] = Field(..., min_items=1, description="System components")
    bindings: List[IntermediateBinding] = Field(default_factory=list, description="Component connections")
    
    # Simplified global configuration
    environment: Literal["development", "staging", "production"] = Field("development", description="Target environment")
    
    @field_validator('name')
    @classmethod
    def validate_system_name(cls, v):
        if not re.match(r'^[a-z][a-z0-9_]*$', v):
            raise ValueError(f"System name '{v}' must be snake_case")
        return v
    
    @field_validator('components')
    @classmethod
    def validate_unique_component_names(cls, v):
        names = [comp.name for comp in v]
        if len(names) != len(set(names)):
            duplicates = [name for name in names if names.count(name) > 1]
            raise ValueError(f"Duplicate component names: {set(duplicates)}")
        return v
    
    @field_validator('bindings')
    @classmethod
    def validate_bindings_reference_existing_components(cls, v, info):
        if 'components' not in info.data:
            return v
        
        component_names = {comp.name for comp in info.data['components']}
        component_ports = {}
        
        # Build port mappings and identify terminal components
        terminal_components = set()
        for comp in info.data['components']:
            component_ports[comp.name] = {
                'inputs': {port.name for port in comp.inputs},
                'outputs': {port.name for port in comp.outputs},
                'type': comp.type
            }
            # Store and Sink components should not have output bindings
            if comp.type in ['Store', 'Sink']:
                terminal_components.add(comp.name)
        
        # Validate each binding
        for binding in v:
            # Check component existence
            if binding.from_component not in component_names:
                raise ValueError(f"Binding references unknown component: {binding.from_component}")
            if binding.to_component not in component_names:
                raise ValueError(f"Binding references unknown component: {binding.to_component}")
            
            # Check if binding is from a terminal component
            if binding.from_component in terminal_components:
                comp_type = component_ports[binding.from_component]['type']
                raise ValueError(
                    f"Component '{binding.from_component}' (type: {comp_type}) cannot have output bindings. "
                    f"Store and Sink components are terminal components with no outputs."
                )
            
            # Check port existence
            if binding.from_port not in component_ports[binding.from_component]['outputs']:
                available = list(component_ports[binding.from_component]['outputs'])
                raise ValueError(f"Component '{binding.from_component}' has no output port '{binding.from_port}'. Available: {available}")
            
            if binding.to_port not in component_ports[binding.to_component]['inputs']:
                available = list(component_ports[binding.to_component]['inputs'])
                raise ValueError(f"Component '{binding.to_component}' has no input port '{binding.to_port}'. Available: {available}")
        
        return v
    
    model_config = {
        "extra": "forbid",  # Prevent unexpected fields
        "json_schema_extra": {
            "example": {
                "name": "simple_data_pipeline",
                "description": "A simple data processing pipeline",
                "version": "1.0.0",
                "components": [
                    {
                        "name": "data_source",
                        "type": "Source",
                        "description": "Reads data from files",
                        "inputs": [],
                        "outputs": [
                            {
                                "name": "data",
                                "schema_type": "object",
                                "description": "Raw data records"
                            }
                        ],
                        "configuration": {
                            "file_path": "/data/input.json",
                            "batch_size": 100
                        }
                    },
                    {
                        "name": "data_transformer",
                        "type": "Transformer",
                        "description": "Transforms data records",
                        "inputs": [
                            {
                                "name": "input",
                                "schema_type": "object",
                                "description": "Input data to transform"
                            }
                        ],
                        "outputs": [
                            {
                                "name": "output",
                                "schema_type": "object",
                                "description": "Transformed data"
                            }
                        ],
                        "configuration": {
                            "transformation_type": "normalize"
                        }
                    },
                    {
                        "name": "data_sink",
                        "type": "Sink",
                        "description": "Writes processed data",
                        "inputs": [
                            {
                                "name": "data",
                                "schema_type": "object",
                                "description": "Data to write"
                            }
                        ],
                        "outputs": [],
                        "configuration": {
                            "output_path": "/data/output.json"
                        }
                    }
                ],
                "bindings": [
                    {
                        "from_component": "data_source",
                        "from_port": "data",
                        "to_component": "data_transformer",
                        "to_port": "input"
                    },
                    {
                        "from_component": "data_transformer",
                        "from_port": "output",
                        "to_component": "data_sink",
                        "to_port": "data"
                    }
                ],
                "environment": "development"
            }
        }
    }


# Helper functions for working with the intermediate format

def validate_intermediate_system(system_dict: Dict[str, Any]) -> IntermediateSystem:
    """Validate and parse a dictionary into an IntermediateSystem"""
    return IntermediateSystem(**system_dict)


def create_simple_example() -> IntermediateSystem:
    """Create a simple example intermediate system"""
    return IntermediateSystem(
        name="hello_world_pipeline",
        description="A minimal example pipeline",
        components=[
            IntermediateComponent(
                name="generator",
                type="Source",
                description="Generates hello world messages",
                outputs=[
                    IntermediatePort(
                        name="message",
                        schema_type="string",
                        description="Hello world message"
                    )
                ],
                configuration={"interval_seconds": 5}
            ),
            IntermediateComponent(
                name="logger",
                type="Sink",
                description="Logs messages to console",
                inputs=[
                    IntermediatePort(
                        name="input",
                        schema_type="string",
                        description="Message to log"
                    )
                ]
            )
        ],
        bindings=[
            IntermediateBinding(
                from_component="generator",
                from_port="message",
                to_component="logger",
                to_port="input"
            )
        ]
    )


def create_complex_example() -> IntermediateSystem:
    """Create a more complex example intermediate system"""
    return IntermediateSystem(
        name="fraud_detection_pipeline",
        description="Real-time fraud detection system with ML scoring",
        version="2.0.0",
        components=[
            IntermediateComponent(
                name="transaction_api",
                type="APIEndpoint",
                description="REST API for receiving transactions",
                outputs=[
                    IntermediatePort(
                        name="transaction",
                        schema_type="object",
                        description="Incoming transaction data"
                    )
                ],
                configuration={
                    "port": 8080,
                    "path": "/api/v1/transactions"
                }
            ),
            IntermediateComponent(
                name="enrichment_service",
                type="Transformer",
                description="Enriches transactions with historical data",
                inputs=[
                    IntermediatePort(
                        name="transaction",
                        schema_type="object",
                        description="Raw transaction"
                    )
                ],
                outputs=[
                    IntermediatePort(
                        name="enriched_transaction",
                        schema_type="object",
                        description="Transaction with additional context"
                    )
                ],
                configuration={
                    "cache_ttl_seconds": 300,
                    "max_history_days": 90
                }
            ),
            IntermediateComponent(
                name="fraud_model",
                type="Model",
                description="ML model for fraud scoring",
                inputs=[
                    IntermediatePort(
                        name="input",
                        schema_type="object",
                        description="Enriched transaction for scoring"
                    )
                ],
                outputs=[
                    IntermediatePort(
                        name="score",
                        schema_type="object",
                        description="Fraud score and metadata"
                    )
                ],
                configuration={
                    "model_path": "/models/fraud_v2.pkl",
                    "threshold": 0.85
                }
            ),
            IntermediateComponent(
                name="risk_router",
                type="Router",
                description="Routes transactions based on risk score",
                inputs=[
                    IntermediatePort(
                        name="scored_transaction",
                        schema_type="object",
                        description="Transaction with fraud score"
                    )
                ],
                outputs=[
                    IntermediatePort(
                        name="high_risk",
                        schema_type="object",
                        description="High risk transactions",
                        required=False
                    ),
                    IntermediatePort(
                        name="low_risk",
                        schema_type="object",
                        description="Low risk transactions",
                        required=False
                    )
                ],
                configuration={
                    "high_risk_threshold": 0.7
                }
            ),
            IntermediateComponent(
                name="alert_system",
                type="Sink",
                description="Sends alerts for high-risk transactions",
                inputs=[
                    IntermediatePort(
                        name="transaction",
                        schema_type="object",
                        description="High-risk transaction requiring alert"
                    )
                ],
                configuration={
                    "alert_channel": "email",
                    "recipients": ["fraud-team@example.com"]
                }
            ),
            IntermediateComponent(
                name="transaction_store",
                type="Store",
                description="Stores all processed transactions",
                inputs=[
                    IntermediatePort(
                        name="transaction",
                        schema_type="object",
                        description="Transaction to store"
                    )
                ],
                configuration={
                    "database": "postgresql",
                    "table": "processed_transactions"
                }
            )
        ],
        bindings=[
            IntermediateBinding(
                from_component="transaction_api",
                from_port="transaction",
                to_component="enrichment_service",
                to_port="transaction"
            ),
            IntermediateBinding(
                from_component="enrichment_service",
                from_port="enriched_transaction",
                to_component="fraud_model",
                to_port="input"
            ),
            IntermediateBinding(
                from_component="fraud_model",
                from_port="score",
                to_component="risk_router",
                to_port="scored_transaction"
            ),
            IntermediateBinding(
                from_component="risk_router",
                from_port="high_risk",
                to_component="alert_system",
                to_port="transaction"
            ),
            IntermediateBinding(
                from_component="risk_router",
                from_port="low_risk",
                to_component="transaction_store",
                to_port="transaction"
            )
        ],
        environment="production"
    )


if __name__ == "__main__":
    # Test the intermediate format
    print("Testing Intermediate Blueprint Format\n")
    
    # Test simple example
    simple = create_simple_example()
    print(f"✅ Simple example validated: {simple.name}")
    print(f"   Components: {len(simple.components)}")
    print(f"   Bindings: {len(simple.bindings)}")
    
    # Test complex example
    complex_example = create_complex_example()
    print(f"\n✅ Complex example validated: {complex_example.name}")
    print(f"   Components: {len(complex_example.components)}")
    print(f"   Bindings: {len(complex_example.bindings)}")
    
    # Test JSON serialization
    import json
    json_str = complex_example.model_dump_json(indent=2)
    print(f"\n📄 JSON representation ({len(json_str)} chars):")
    print(json_str[:500] + "..." if len(json_str) > 500 else json_str)
    
    # Test validation errors
    print("\n🧪 Testing validation errors:")
    try:
        invalid = IntermediateSystem(
            name="Invalid-Name",  # Should fail: uppercase not allowed
            description="Test",
            components=[]
        )
    except Exception as e:
        print(f"   ✅ Caught expected error: {e}")