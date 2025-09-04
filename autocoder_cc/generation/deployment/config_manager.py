"""
Configuration Manager for Dynamic Configuration Detection & Management
REFACTOR Phase: Clean implementation without duplication
"""
import ast
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ConfigRequirement:
    """Data class representing a configuration requirement"""
    key: str
    required: bool
    config_type: str
    default: Any = None
    description: str = ""


class ConfigurationAnalyzer:
    """
    Analyzes generated components to extract configuration requirements
    
    This class focuses solely on analyzing component code to detect configuration
    requirements. Environment-specific configuration generation is handled by
    EnvironmentTemplateManager to avoid duplication.
    
    Features:
    - AST-based analysis of Python code
    - Detection of required vs optional configurations
    - Type inference and validation
    - Comprehensive error handling
    """
    
    # Class-level constants for better maintainability
    DEFAULT_TYPE = "string"
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_component_requirements(self, component_code: str) -> Dict[str, Dict[str, Any]]:
        """
        Analyze component code to extract configuration requirements
        
        Args:
            component_code: Python source code of the component
            
        Returns:
            Dictionary mapping config keys to their requirements
            
        Raises:
            SyntaxError: If component code has invalid Python syntax
        """
        if not component_code.strip():
            return {}
            
        try:
            tree = ast.parse(component_code)
            self.logger.debug(f"Successfully parsed {len(component_code)} characters of component code")
        except SyntaxError as e:
            self.logger.error(f"Failed to parse component code: {e}")
            raise SyntaxError(f"Invalid Python syntax in component code: {e}")
            
        requirements = {}
        config_calls = self._extract_config_calls(tree)
        
        for call_info in config_calls:
            config_key = call_info["key"]
            has_default = call_info["has_default"]
            default_value = call_info["default_value"]
            
            requirements[config_key] = {
                "required": not has_default,
                "type": self._infer_type(default_value) if has_default else self.DEFAULT_TYPE
            }
            
            if has_default:
                requirements[config_key]["default"] = default_value
                
        self.logger.info(f"Extracted {len(requirements)} configuration requirements")
        return requirements
    
    def _extract_config_calls(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract all config.get() calls from the AST"""
        config_calls = []
        
        for node in ast.walk(tree):
            if self._is_config_get_call(node):
                call_info = self._parse_config_call(node)
                if call_info:
                    config_calls.append(call_info)
                    
        return config_calls
    
    def _is_config_get_call(self, node: ast.AST) -> bool:
        """Check if a node represents a config.get() call"""
        return (isinstance(node, ast.Call) and
                isinstance(node.func, ast.Attribute) and
                node.func.attr == 'get' and
                isinstance(node.func.value, ast.Name) and
                node.func.value.id == 'config')
    
    def _parse_config_call(self, node: ast.Call) -> Optional[Dict[str, Any]]:
        """Parse a config.get() call to extract key and default value"""
        if not node.args or not isinstance(node.args[0], ast.Constant):
            return None
            
        config_key = node.args[0].value
        has_default = len(node.args) > 1
        default_value = None
        
        if has_default and isinstance(node.args[1], ast.Constant):
            default_value = node.args[1].value
            
        return {
            "key": config_key,
            "has_default": has_default,
            "default_value": default_value
        }
    
    def _infer_type(self, value: Any) -> str:
        """Infer the type of a configuration value with better type detection"""
        type_mapping = {
            bool: "bool",
            int: "int", 
            float: "float",
            str: "string"
        }
        return type_mapping.get(type(value), self.DEFAULT_TYPE)