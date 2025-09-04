#!/usr/bin/env python3
"""
FocusedPromptEngine - Generate concise business-logic-only prompts

This module creates focused prompts for LLM generation that contain ONLY
business requirements without boilerplate code or infrastructure details.
"""

from typing import Dict, Any
from .business_logic_spec import BusinessLogicSpec


class FocusedPromptEngine:
    """
    Generates focused prompts for business logic implementation.
    
    Creates concise prompts that request only the core business transformation
    method, excluding all boilerplate and infrastructure concerns.
    """
    
    def generate_business_logic_prompt(self, business_spec: BusinessLogicSpec) -> str:
        """
        Generate a focused prompt for business logic implementation.
        
        Args:
            business_spec: Business requirements extracted from blueprint
            
        Returns:
            Concise prompt requesting only business logic method implementation
        """
        prompt_parts = []
        
        # Core instruction - request method only
        prompt_parts.append(
            f"Implement the async def process_item method for {business_spec.component_name} ({business_spec.component_type})."
        )
        
        # Business purpose
        prompt_parts.append(f"Purpose: {business_spec.business_purpose}")
        
        # Transformation specification
        prompt_parts.append(f"Transform: {business_spec.transformation_description}")
        
        # Input/output specification
        if business_spec.input_schema:
            input_desc = self._format_schema_description(business_spec.input_schema)
            prompt_parts.append(f"Input: {input_desc}")
            
        if business_spec.output_schema:
            output_desc = self._format_schema_description(business_spec.output_schema)
            prompt_parts.append(f"Output: {output_desc}")
        
        # Requirements
        requirements = []
        
        # Edge cases
        if business_spec.edge_cases:
            requirements.extend(business_spec.edge_cases)
            
        # Quality requirements
        if business_spec.quality_requirements:
            for key, value in business_spec.quality_requirements.items():
                requirements.append(f"{key}: {value}")
        
        # Validation rules
        if business_spec.validation_rules:
            requirements.extend(business_spec.validation_rules)
            
        if requirements:
            prompt_parts.append(f"Requirements: {'; '.join(requirements)}")
        
        # Method signature instruction
        prompt_parts.append(
            "Return only the method implementation with signature: "
            "async def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:"
        )
        
        return "\n".join(prompt_parts)
    
    def _format_schema_description(self, schema: Dict[str, Any]) -> str:
        """Format schema into concise description"""
        if not schema:
            return ""
            
        schema_parts = []
        for field_name, field_info in schema.items():
            if isinstance(field_info, dict):
                field_type = field_info.get('type', 'object')
                description = field_info.get('description', '')
                required = field_info.get('required', True)
                
                field_desc = f"{field_name}: {field_type}"
                if description:
                    field_desc += f" ({description})"
                if not required:
                    field_desc += " [optional]"
                    
                schema_parts.append(field_desc)
            else:
                # Simple string schema
                schema_parts.append(f"{field_name}: {field_info}")
                
        return "{" + ", ".join(schema_parts) + "}"