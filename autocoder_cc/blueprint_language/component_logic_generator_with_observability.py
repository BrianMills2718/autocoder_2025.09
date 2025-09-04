#!/usr/bin/env python3
"""
Component Logic Generator with Enhanced Observability

This is a wrapper around the existing ComponentLogicGenerator that adds
comprehensive logging for debugging generation failures.

Author: Claude (Anthropic)
Date: 2025-08-10
"""
import ast
from pathlib import Path
from typing import Dict, Any, Optional
from autocoder_cc.observability.generation_logger import GenerationLogger, observable
from autocoder_cc.blueprint_language.component_logic_generator import ComponentLogicGenerator as BaseGenerator


class ObservableComponentLogicGenerator(BaseGenerator):
    """
    Enhanced ComponentLogicGenerator with comprehensive observability.
    
    This wraps the existing generator to add detailed logging at every stage
    without modifying the original implementation.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._generation_logger = GenerationLogger()
        self.logger.info("Observable Component Logic Generator initialized")
    
    @observable("generate_component", capture_args=True, capture_result=True)
    async def _generate_component(self, component: Any, blueprint: Dict[str, Any]) -> Any:
        """
        Wrapped component generation with observability.
        """
        component_name = component.name
        
        # Log component specification
        self._generation_logger.log_template_render(
            component_name=component_name,
            template_name="component_spec",
            input_data={
                "type": component.type,
                "description": getattr(component, 'description', ''),
                "inputs": getattr(component, 'inputs', []),
                "outputs": getattr(component, 'outputs', []),
                "config": getattr(component, 'config', {})
            },
            output=""  # Will be filled by LLM
        )
        
        # Call parent implementation
        return await super()._generate_component(component, blueprint)
    
    def _write_component_file(self, component: Any, component_file: Path) -> None:
        """
        Wrapped file writing with observability.
        """
        component_name = component.name
        
        # Log AST validation
        self._generation_logger.start_stage("ast_validation", component_name)
        
        try:
            # Validate AST
            parsed_ast = ast.parse(component.implementation)
            self._generation_logger.end_stage(
                "ast_validation", 
                component_name,
                ast_nodes=len(parsed_ast.body),
                success=True
            )
        except SyntaxError as e:
            self._generation_logger.log_validation_error(
                component_name=component_name,
                error_type="SyntaxError",
                error_message=str(e),
                line_number=e.lineno,
                code_context=e.text
            )
            raise
        
        # Log file write
        self._generation_logger.log_file_write(
            component_name=component_name,
            file_path=str(component_file),
            content=component.implementation
        )
        
        # Call parent implementation
        super()._write_component_file(component, component_file)
    
    async def _call_llm_for_component(self, 
                                     component_type: str,
                                     component_name: str,
                                     component_description: str,
                                     component_config: Dict[str, Any],
                                     system_context: str) -> str:
        """
        Wrapped LLM call with observability.
        """
        # Build prompt (this is a simplified version - actual may differ)
        prompt = f"""
Generate a {component_type} component named {component_name}.
Description: {component_description}
Config: {component_config}
System Context: {system_context}

Please generate a complete Python implementation.
"""
        
        self._generation_logger.start_stage("llm_request", component_name)
        
        try:
            # Call parent's LLM method (if it exists)
            if hasattr(super(), '_call_llm_for_component'):
                response = await super()._call_llm_for_component(
                    component_type, component_name, component_description,
                    component_config, system_context
                )
            else:
                # Fallback to direct LLM call
                response = await self.llm_generator.generate_component_implementation(
                    component_type=component_type,
                    component_name=component_name,
                    component_description=component_description,
                    component_config=component_config,
                    class_name=component_name.replace('_', '').title()
                )
            
            # Log the interaction
            self._generation_logger.log_llm_interaction(
                component_name=component_name,
                prompt=prompt,
                response=response,
                model=getattr(self.llm_generator, 'model_name', 'unknown'),
                tokens_in=len(prompt.split()),  # Rough estimate
                tokens_out=len(response.split())  # Rough estimate
            )
            
            self._generation_logger.end_stage(
                "llm_request",
                component_name,
                response_length=len(response),
                success=True
            )
            
            return response
            
        except Exception as e:
            self._generation_logger.log_error("llm_request", component_name, e)
            raise
    
    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of the generation session.
        """
        return self._generation_logger.generate_summary()


def patch_existing_generator():
    """
    Monkey-patch the existing ComponentLogicGenerator to add observability.
    
    This function can be called to enhance an existing generator instance
    without changing its code.
    """
    import functools
    from autocoder_cc.blueprint_language import component_logic_generator
    
    original_generate = component_logic_generator.ComponentLogicGenerator._generate_component
    original_write = component_logic_generator.ComponentLogicGenerator._write_component_file
    
    logger = GenerationLogger()
    
    @functools.wraps(original_generate)
    async def wrapped_generate(self, component, blueprint):
        logger.start_stage("component_generation", component.name)
        try:
            result = await original_generate(self, component, blueprint)
            logger.end_stage("component_generation", component.name, success=True)
            return result
        except Exception as e:
            logger.log_error("component_generation", component.name, e)
            raise
    
    @functools.wraps(original_write)
    def wrapped_write(self, component, component_file):
        logger.log_file_write(
            component_name=component.name,
            file_path=str(component_file),
            content=component.implementation[:1000]  # Preview
        )
        return original_write(self, component, component_file)
    
    # Apply patches
    component_logic_generator.ComponentLogicGenerator._generate_component = wrapped_generate
    component_logic_generator.ComponentLogicGenerator._write_component_file = wrapped_write
    
    return logger


def fix_import_template():
    """
    Fix the hardcoded import template that causes failures.
    
    This patches the incorrect import path in the component generation template.
    """
    from autocoder_cc.blueprint_language import component_logic_generator
    
    # The correct import path
    CORRECT_IMPORT = "from autocoder_cc.components.composed_base import ComposedComponent"
    
    # Find and fix the template in _write_component_file
    if hasattr(component_logic_generator.ComponentLogicGenerator, '_write_component_file'):
        import inspect
        source = inspect.getsource(component_logic_generator.ComponentLogicGenerator._write_component_file)
        
        # Log what we found
        logger = GenerationLogger()
        logger.logger.info(
            "import_template_analysis",
            has_wrong_import="from observability import" in source,
            correct_import_needed=CORRECT_IMPORT
        )
        
        # Return the fix that needs to be applied
        return {
            "found_issue": "from observability import" in source,
            "wrong_import": "from observability import ComposedComponent",
            "correct_import": CORRECT_IMPORT,
            "file_to_fix": component_logic_generator.__file__,
            "line_to_fix": 1492  # Based on our earlier investigation
        }
    
    return None


if __name__ == "__main__":
    # Example usage
    print("Observable Component Logic Generator")
    print("=====================================")
    
    # Check import template issue
    fix_info = fix_import_template()
    if fix_info and fix_info["found_issue"]:
        print(f"\n❌ Found import issue in {fix_info['file_to_fix']}")
        print(f"   Line {fix_info['line_to_fix']}: {fix_info['wrong_import']}")
        print(f"   Should be: {fix_info['correct_import']}")
    else:
        print("\n✅ Import template appears correct")
    
    # Example of patching existing generator
    print("\n📊 Patching existing generator for observability...")
    logger = patch_existing_generator()
    print(f"   Session ID: {logger.session_id}")
    print(f"   Log directory: {logger.log_dir}")
    
    print("\nObservability enhancements installed successfully!")
    print("Logs will be written to:", logger.log_dir)