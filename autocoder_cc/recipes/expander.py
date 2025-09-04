"""Recipe expander that converts recipes into full component implementations."""
from typing import Dict, Any, Optional
from .registry import get_recipe, RECIPE_REGISTRY
from autocoder_cc.errors.error_codes import RecipeError, ErrorCode

class RecipeExpander:
    """Expands recipes into complete component code.
    
    The expander takes a recipe definition and generates a complete
    Python component class that inherits from the appropriate primitive.
    """
    
    def expand_recipe(self, recipe_name: str, component_name: str, 
                     config: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate ONLY component structure. LLM MUST generate ALL implementations.
        NO STUB METHODS ALLOWED.
        
        Args:
            recipe_name: Name of recipe (e.g., "Store", "Controller")
            component_name: Name for the component instance (e.g., "user_store", "todo_controller")
            config: Configuration to merge with recipe defaults
            
        Returns:
            Generated Python code skeleton for LLM to implement
            
        Raises:
            RecipeError: If recipe not found or expansion fails
        """
        try:
            recipe = get_recipe(recipe_name)
        except ValueError as e:
            raise RecipeError(
                ErrorCode.RECIPE_NOT_FOUND,
                f"Recipe '{recipe_name}' not found",
                {"available_recipes": list(RECIPE_REGISTRY.keys())}
            )
        base_primitive = recipe["base_primitive"]
        
        # Merge configs (user config overrides recipe defaults)
        final_config = {**recipe.get("config", {}), **(config or {})}
        
        # Generate imports
        imports = [
            f"from autocoder_cc.components.primitives import {base_primitive}",
            "from autocoder_cc.components.ports import InputPort, OutputPort",
            "from autocoder_cc.observability import get_logger",
            "from autocoder_cc.errors.error_codes import ErrorCode",
            "from typing import Dict, Any, Optional, List",
            "import anyio"
        ]
        imports.extend(recipe.get("imports", []))
        
        # Generate class name (PascalCase)
        class_name = ''.join(word.capitalize() for word in component_name.split('_'))
        
        # Start generating class
        code_lines = [
            '"""',
            f'Component: {class_name}',
            f'Recipe: {recipe_name}',
            f'Description: {recipe.get("description", "Component generated from recipe")}',
            '"""',
            '',
            '\n'.join(imports),
            '',
            f'class {class_name}({base_primitive}):',
            f'    """',
            f'    {recipe.get("description", "Component generated from recipe")}',
            f'    ',
            f'    Generated from recipe: {recipe_name}',
            f'    Base primitive: {base_primitive}',
            f'    """',
            f'    ',
            f'    def __init__(self, name: str = "{component_name}", config: Dict[str, Any] = None):',
            f'        """Initialize {class_name}."""',
            f'        default_config = {final_config!r}',
            f'        merged_config = {{**default_config, **(config or {{}})}}',
            f'        super().__init__(name, merged_config)',
            f'        self.logger = get_logger(self.__class__.__name__)',
            f'        self._setup_ports()',
            f'    ',
            f'    def _setup_ports(self):',
            f'        """Configure ports based on recipe."""'
        ]
        
        # Add port setup based on primitive type
        ports = recipe.get("ports", {})
        
        if base_primitive == "Transformer":
            # Transformer has one input and one output
            if "input" in ports:
                port_info = ports["input"]
                code_lines.append(f'        self.input_port = InputPort("{port_info["name"]}", dict)')
            if "output" in ports:
                port_info = ports["output"]
                code_lines.append(f'        self.output_port = OutputPort("{port_info["name"]}", dict)')
                
        elif base_primitive == "Source":
            # Source has only outputs
            if "outputs" in ports:
                for port_name, port_info in ports["outputs"].items():
                    code_lines.append(f'        self.{port_name} = OutputPort("{port_name}", dict)')
                    
        elif base_primitive == "Sink":
            # Sink has only inputs
            if "inputs" in ports:
                for port_name, port_info in ports["inputs"].items():
                    code_lines.append(f'        self.{port_name} = InputPort("{port_name}", dict)')
                    
        elif base_primitive == "Splitter":
            # Splitter has one input and multiple outputs
            if "input" in ports:
                port_info = ports["input"]
                code_lines.append(f'        self.input_port = InputPort("{port_info["name"]}", dict)')
            if "outputs" in ports:
                code_lines.append('        self.output_ports = {}')
                for port_name, port_info in ports["outputs"].items():
                    code_lines.append(f'        self.output_ports["{port_name}"] = OutputPort("{port_name}", dict)')
                    
        elif base_primitive == "Merger":
            # Merger has multiple inputs and one output
            if "inputs" in ports:
                code_lines.append('        self.input_ports = {}')
                for port_name, port_info in ports["inputs"].items():
                    code_lines.append(f'        self.input_ports["{port_name}"] = InputPort("{port_name}", dict)')
            if "output" in ports:
                port_info = ports["output"]
                code_lines.append(f'        self.output_port = OutputPort("{port_info["name"]}", dict)')
        
        code_lines.append('    ')
        
        # DO NOT ADD METHOD IMPLEMENTATIONS FROM RECIPE
        # The LLM must generate ALL implementations from scratch
        # Including recipe methods causes the LLM to generate stubs for referenced helper methods
        
        # Add placeholder for primary method based on primitive type
        if base_primitive == "Transformer":
            code_lines.append('    async def transform(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:')
            code_lines.append('        """Transform data. LLM MUST implement this."""')
            code_lines.append('        # LLM MUST GENERATE COMPLETE IMPLEMENTATION')
            code_lines.append('        raise NotImplementedError("LLM must implement transform method")')
            
        elif base_primitive == "Source":
            code_lines.append('    async def generate(self):')
            code_lines.append('        """Generate data. LLM MUST implement this."""')
            code_lines.append('        # LLM MUST GENERATE COMPLETE IMPLEMENTATION')
            code_lines.append('        raise NotImplementedError("LLM must implement generate method")')
            
        elif base_primitive == "Sink":
            code_lines.append('    async def consume(self, data: Dict[str, Any]):')
            code_lines.append('        """Consume data. LLM MUST implement this."""')
            code_lines.append('        # LLM MUST GENERATE COMPLETE IMPLEMENTATION')
            code_lines.append('        raise NotImplementedError("LLM must implement consume method")')
            
        elif base_primitive == "Splitter":
            code_lines.append('    async def split(self, data: Dict[str, Any]) -> Dict[str, Any]:')
            code_lines.append('        """Split data to outputs. LLM MUST implement this."""')
            code_lines.append('        # LLM MUST GENERATE COMPLETE IMPLEMENTATION')
            code_lines.append('        raise NotImplementedError("LLM must implement split method")')
            
        elif base_primitive == "Merger":
            code_lines.append('    async def merge(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:')
            code_lines.append('        """Merge multiple inputs. LLM MUST implement this."""')
            code_lines.append('        # LLM MUST GENERATE COMPLETE IMPLEMENTATION')
            code_lines.append('        raise NotImplementedError("LLM must implement merge method")')
        
        # NO STUB METHODS - LLM MUST GENERATE ALL IMPLEMENTATIONS
        code_lines.extend([
            '    ',
            '    # LLM MUST IMPLEMENT ALL METHODS WITH REAL FUNCTIONALITY',
            '    # NO STUBS, NO SIMPLIFIED IMPLEMENTATIONS, NO ALWAYS-TRUE RETURNS',
            '    ',
            '    async def setup(self):',
            '        """Initialize the component."""',
            '        await super().setup()',
            '        # LLM MUST ADD: Real initialization logic here',
            '        raise NotImplementedError(',
            f'            "[{ErrorCode.RECIPE_NO_IMPLEMENTATION.value}] "',
            '            "LLM must generate real implementation. Recipe only provides structure."',
            '        )',
            '    ',
            '    async def cleanup(self):',
            '        """Clean up resources."""',
            '        # LLM MUST ADD: Real cleanup logic here',
            '        raise NotImplementedError(',
            f'            "[{ErrorCode.RECIPE_NO_IMPLEMENTATION.value}] "',
            '            "LLM must generate real cleanup implementation."',
            '        )'
        ])
        
        return '\n'.join(code_lines)
    
    def validate_recipe(self, recipe_name: str) -> bool:
        """
        Validate a recipe has all required fields.
        
        Args:
            recipe_name: Name of recipe to validate
            
        Returns:
            True if recipe is valid
        """
        try:
            recipe = get_recipe(recipe_name)
            required = ["base_primitive", "description", "ports"]
            return all(field in recipe for field in required)
        except ValueError:
            return False
    
    def expand_to_spec(self, recipe_name: str, component_name: str, 
                       config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Expand a recipe into a component specification dictionary.
        
        Returns:
            Component specification dict with type, config, ports, etc.
        """
        recipe = get_recipe(recipe_name)
        
        spec = {
            'name': component_name,
            'type': recipe.get('base_primitive'),
            'config': {**recipe.get('config', {}), **(config or {})},
            'description': recipe.get('description', ''),
        }
        
        # Add ports if defined
        if 'ports' in recipe:
            if 'inputs' in recipe['ports']:
                spec['inputs'] = recipe['ports']['inputs']
            if 'outputs' in recipe['ports']:
                spec['outputs'] = recipe['ports']['outputs']
                
        return spec
    
    def get_recipe_info(self, recipe_name: str) -> Dict[str, Any]:
        """
        Get information about a recipe.
        
        Args:
            recipe_name: Name of recipe
            
        Returns:
            Recipe information dict
        """
        recipe = get_recipe(recipe_name)
        return {
            "name": recipe_name,
            "base_primitive": recipe["base_primitive"],
            "description": recipe.get("description", ""),
            "ports": recipe.get("ports", {}),
            "config_options": list(recipe.get("config", {}).keys())
        }