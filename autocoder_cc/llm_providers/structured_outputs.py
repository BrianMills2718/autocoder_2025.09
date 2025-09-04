"""
Pydantic models for structured LLM outputs
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class ComponentType(str, Enum):
    """Supported component types"""
    SOURCE = "Source"
    TRANSFORMER = "Transformer"
    SINK = "Sink"
    STORE = "Store"
    API_ENDPOINT = "APIEndpoint"
    CONTROLLER = "Controller"
    STREAM_PROCESSOR = "StreamProcessor"
    MODEL = "Model"
    ROUTER = "Router"
    FILTER = "Filter"
    AGGREGATOR = "Aggregator"
    ACCUMULATOR = "Accumulator"
    WEBSOCKET = "WebSocket"


class MethodDefinition(BaseModel):
    """Represents a method in the component"""
    model_config = {"extra": "forbid", "json_schema_extra": {"additionalProperties": False}}
    
    name: str = Field(description="Method name")
    async_method: bool = Field(default=False, description="Whether this is an async method")
    parameters: List[str] = Field(default_factory=lambda: ["self"], description="Method parameters including self")
    docstring: str = Field(default="", description="Method docstring")
    body: str = Field(description="Method implementation body")
    decorators: Optional[List[str]] = Field(default=None, description="Method decorators")
    signature: Optional[str] = Field(default=None, description="Alternative to parameters - full signature string")


class GeneratedComponent(BaseModel):
    """Structured output for component generation"""
    model_config = {"extra": "forbid", "json_schema_extra": {"additionalProperties": False}}
    
    component_type: ComponentType = Field(description="Type of component being generated")
    class_name: str = Field(description="Name of the component class")
    base_class: str = Field(description="Base class to inherit from")
    docstring: str = Field(description="Class-level docstring")
    
    # Initialization - use string instead of Dict for simplicity
    init_attributes: str = Field(
        default="",
        description="JSON string of attributes to initialize in __init__"
    )
    
    # Core methods
    setup_body: str = Field(description="Implementation of the setup() method body")
    process_body: str = Field(description="Implementation of the process() method body")
    cleanup_body: Optional[str] = Field(default=None, description="Implementation of the cleanup() method body")
    health_check_body: Optional[str] = Field(default=None, description="Implementation of the health_check() method body")
    
    # Additional methods
    helper_methods: Optional[List[MethodDefinition]] = Field(
        default=None,
        description="Additional helper methods"
    )
    
    # Imports needed (beyond base imports)
    additional_imports: Optional[List[str]] = Field(
        default=None,
        description="Additional import statements needed"
    )
    
    # Configuration validation - use string instead of Dict
    config_schema: Optional[str] = Field(
        default=None,
        description="JSON string of configuration schema for validation"
    )


class ComponentGenerationRequest(BaseModel):
    """Request structure for component generation"""
    component_type: ComponentType
    component_name: str
    component_description: str
    configuration: Dict[str, Any] = Field(default_factory=dict)
    inputs: Optional[List[Dict[str, str]]] = None
    outputs: Optional[List[Dict[str, str]]] = None
    system_context: Optional[str] = None


class ValidationResult(BaseModel):
    """Result of code validation"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class CodeFixRequest(BaseModel):
    """Request to fix code issues"""
    original_code: str
    validation_errors: List[str]
    component_context: ComponentGenerationRequest


class CodeFixResponse(BaseModel):
    """Fixed code response"""
    fixed_code: GeneratedComponent
    changes_made: List[str]
    confidence_score: float = Field(ge=0.0, le=1.0)