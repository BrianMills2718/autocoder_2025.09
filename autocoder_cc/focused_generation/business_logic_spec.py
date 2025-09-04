#!/usr/bin/env python3
"""
BusinessLogicSpec - Data structure for focused LLM generation

This dataclass captures only the business requirements from blueprint components,
enabling focused LLM prompts without boilerplate code or infrastructure details.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class BusinessLogicSpec:
    """
    Captures business logic requirements for focused LLM generation.
    
    This dataclass contains only the essential business requirements needed
    to generate the core transformation logic, excluding all infrastructure
    and boilerplate concerns.
    """
    
    # Core identification
    component_name: str
    component_type: str  # Source, Transformer, Sink, Store, APIEndpoint, Router
    business_purpose: str
    
    # Data transformation specification
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    transformation_description: str
    
    # Optional business requirements
    edge_cases: List[str] = field(default_factory=list)
    quality_requirements: Dict[str, Any] = field(default_factory=dict)
    validation_rules: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate required fields are not empty"""
        if not self.business_purpose.strip():
            raise ValueError("business_purpose is required and cannot be empty")
        if not self.transformation_description.strip():
            raise ValueError("transformation_description is required and cannot be empty")
            
    def to_prompt_context(self) -> str:
        """
        Generate focused prompt context for LLM generation.
        
        Returns concise business requirements suitable for focused LLM prompts
        without any infrastructure or boilerplate concerns.
        """
        context_parts = []
        
        # Core purpose and transformation
        context_parts.append(f"Component: {self.component_name} ({self.component_type})")
        context_parts.append(f"Purpose: {self.business_purpose}")
        context_parts.append(f"Transformation: {self.transformation_description}")
        
        # Input/output specification
        if self.input_schema:
            input_fields = ", ".join(f"{k}: {v}" for k, v in self.input_schema.items())
            context_parts.append(f"Input: {input_fields}")
            
        if self.output_schema:
            output_fields = ", ".join(f"{k}: {v}" for k, v in self.output_schema.items())
            context_parts.append(f"Output: {output_fields}")
        
        # Edge cases and requirements
        if self.edge_cases:
            context_parts.append(f"Edge cases: {'; '.join(self.edge_cases)}")
            
        if self.quality_requirements:
            quality_items = [f"{k}: {v}" for k, v in self.quality_requirements.items()]
            context_parts.append(f"Quality requirements: {'; '.join(quality_items)}")
            
        if self.validation_rules:
            context_parts.append(f"Validation rules: {'; '.join(self.validation_rules)}")
        
        return "\n".join(context_parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "component_name": self.component_name,
            "component_type": self.component_type,
            "business_purpose": self.business_purpose,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "transformation_description": self.transformation_description,
            "edge_cases": self.edge_cases,
            "quality_requirements": self.quality_requirements,
            "validation_rules": self.validation_rules
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BusinessLogicSpec":
        """Create from dictionary for deserialization"""
        return cls(
            component_name=data["component_name"],
            component_type=data["component_type"],
            business_purpose=data["business_purpose"],
            input_schema=data["input_schema"],
            output_schema=data["output_schema"],
            transformation_description=data["transformation_description"],
            edge_cases=data.get("edge_cases", []),
            quality_requirements=data.get("quality_requirements", {}),
            validation_rules=data.get("validation_rules", [])
        )