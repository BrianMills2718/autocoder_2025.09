"""
O3-Specialized Prompt Engineering

This module contains prompt engineering specifically optimized for O3 reasoning models.
O3 models work differently from other LLMs - they use internal reasoning and don't support
temperature parameters.

Key Features:
- Simplified, direct prompts that work better with O3's reasoning process
- Progressive prompt improvement for retry scenarios
- Anti-placeholder prompt engineering
- Maximum context prompts for final attempts
"""

import json
from typing import Dict, Any


class O3PromptEngine:
    """
    Specialized prompt engineering for O3 reasoning models
    
    O3 models require different prompt strategies:
    - Simple, direct instructions work better than complex reasoning checkpoints
    - Clear structure and requirements
    - Explicit prohibition of placeholder patterns
    """
    
    def __init__(self):
        self.reasoning_prefix = self._build_reasoning_prefix()
    
    def _build_reasoning_prefix(self) -> str:
        """Get O3-specific reasoning prefix - simplified for better results"""
        return """Generate a complete, working Python component. 

Think step by step:
1. Include the full embedded base class code first
2. Create the component class that inherits from ComposedComponent  
3. Implement ALL methods with real business logic (no placeholders)
4. Ensure perfect Python syntax

"""
    
    def get_o3_optimized_prompt(self, component_type: str, context: Dict[str, Any]) -> str:
        """
        Simplified O3-specific prompt - direct and focused for better results
        
        Args:
            component_type: The type of component to generate
            context: Context information for the component
            
        Returns:
            Optimized prompt string for O3 models
        """
        base_prompt = f"""
Generate a complete {component_type} component with these requirements:

FORBIDDEN: return {{"value": 42}}, TODO, FIXME, NotImplementedError, pass statements, localhost

REQUIRED STRUCTURE:
1. All imports at top
2. Complete embedded base class code (ComposedComponent, etc.)
3. Component class inheriting from ComposedComponent
4. Real business logic in process_item method
5. Perfect Python syntax

Component: {component_type}
Config: {context}

Output ONLY valid Python code starting with imports.
"""
        return base_prompt
    
    def build_anti_placeholder_prompt(self, component_type: str, context: Dict[str, Any]) -> str:
        """
        Simplified anti-placeholder prompt for better o3 results
        
        Used when previous generation attempts contained placeholder code.
        
        Args:
            component_type: The type of component to generate
            context: Context information for the component
            
        Returns:
            Anti-placeholder prompt string
        """
        return f"""
Previous generation had placeholder code. Fix this:

FORBIDDEN: return {{"value": 42}}, TODO, FIXME, NotImplementedError, pass, localhost

Generate a complete working {component_type} with:
- Full embedded base class code
- Component class with real business logic
- Complete process_item method implementation
- Proper error handling
- Valid Python syntax

Context: {context}

Start with imports, end with working component class.
"""
    
    def build_maximum_context_prompt(self, component_type: str, context: Dict[str, Any]) -> str:
        """
        Simplified final attempt prompt for o3
        
        Used as a last resort when all other generation attempts have failed.
        
        Args:
            component_type: The type of component to generate
            context: Context information for the component
            
        Returns:
            Maximum context prompt string for final attempt
        """
        return f"""
FINAL ATTEMPT - Generate complete working Python code.

Type: {component_type}
Config: {json.dumps(context, indent=2)}

REQUIREMENTS:
1. Include full embedded base class code first
2. Create component class inheriting from ComposedComponent  
3. Implement process_item method with real business logic
4. Use Docker service names (not localhost)
5. Perfect Python syntax - no errors
6. NO placeholder patterns: return {{"value": 42}}, TODO, NotImplementedError

Generate complete Python file starting with imports.
"""
    
    def get_reasoning_prefix(self) -> str:
        """Get the O3 reasoning prefix for prompt enhancement"""
        return self.reasoning_prefix
    
    def is_o3_model(self, model_name: str) -> bool:
        """
        Check if the given model name is an O3 model
        
        Args:
            model_name: Name of the model to check
            
        Returns:
            True if it's an O3 model, False otherwise
        """
        o3_models = ["o3", "o3-mini"]
        return model_name in o3_models
    
    def get_progressive_prompt(self, attempt: int, component_type: str, context: Dict[str, Any], 
                              validation_feedback: str = "") -> str:
        """
        Get progressively improved prompts based on attempt number
        
        Args:
            attempt: Current attempt number (0-based)
            component_type: Type of component to generate
            context: Context information
            validation_feedback: Feedback from previous validation failures
            
        Returns:
            Appropriate prompt for the current attempt
        """
        if attempt == 0:
            return self.get_o3_optimized_prompt(component_type, context)
        elif attempt == 1:
            return self.build_anti_placeholder_prompt(component_type, context)
        else:
            return self.build_maximum_context_prompt(component_type, context)