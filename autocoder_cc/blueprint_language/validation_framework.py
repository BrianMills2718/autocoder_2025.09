"""Multi-level validation framework for system generation."""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import ast
import asyncio
from autocoder_cc.observability import get_logger
from .validation_result_types import ValidationResult, ValidationFailure, ValidationSeverity


class ValidationFramework:
    """Multi-level validation framework for generated systems."""
    
    def __init__(self):
        """Initialize validation framework."""
        self.logger = get_logger("ValidationFramework")
        self.validation_levels = {
            "syntax": self.validate_syntax,
            "structure": self.validate_structure,
            "contracts": self.validate_contracts,
            "integration": self.validate_integration
        }
        
    async def validate_component(self, component_code: str, component_name: str, 
                                level: str = "all") -> ValidationResult:
        """Validate a component at specified levels.
        
        Args:
            component_code: Component source code
            component_name: Name of the component
            level: Validation level ('syntax', 'structure', 'contracts', 'integration', or 'all')
            
        Returns:
            ValidationResult with validation outcome
        """
        result = ValidationResult(success=True)
        
        if level == "all":
            levels_to_run = list(self.validation_levels.keys())
        elif level in self.validation_levels:
            levels_to_run = [level]
        else:
            result.add_failure(f"Unknown validation level: {level}", ValidationSeverity.ERROR)
            return result
            
        for level_name in levels_to_run:
            validator = self.validation_levels[level_name]
            level_result = await validator(component_code, component_name)
            result.merge(level_result)
            
        if result.success:
            self.logger.info(f"✅ All validations passed for {component_name}")
        else:
            self.logger.error(f"❌ Validation failed for {component_name}: {len(result.failures)} errors")
            
        return result
        
    async def validate_syntax(self, code: str, name: str) -> ValidationResult:
        """Validate Python syntax.
        
        Args:
            code: Source code to validate
            name: Component name for error reporting
            
        Returns:
            ValidationResult with syntax validation outcome
        """
        result = ValidationResult(success=True)
        
        try:
            ast.parse(code)
            self.logger.debug(f"Syntax valid for {name}")
        except SyntaxError as e:
            result.add_failure(
                f"Syntax error at line {e.lineno}: {e.msg}",
                ValidationSeverity.ERROR,
                f"{name}.py:{e.lineno}",
                {"error": str(e)}
            )
            
        return result
        
    async def validate_structure(self, code: str, name: str) -> ValidationResult:
        """Validate component structure (required methods, inheritance).
        
        Args:
            code: Source code to validate
            name: Component name
            
        Returns:
            ValidationResult with structure validation outcome
        """
        result = ValidationResult(success=True)
        
        try:
            tree = ast.parse(code)
            
            # Find class definition
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            if not classes:
                result.add_failure(
                    "No class definition found",
                    ValidationSeverity.ERROR,
                    name
                )
                return result
                
            main_class = classes[0]
            
            # Check for required methods
            methods = {node.name for node in main_class.body if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef)}
            
            required_methods = ["setup", "process", "cleanup"]
            for method in required_methods:
                if method not in methods:
                    result.add_failure(
                        f"Missing required method: {method}",
                        ValidationSeverity.WARNING,
                        f"{name}.{main_class.name}"
                    )
                    
            # Check for proper inheritance
            if not main_class.bases:
                result.add_failure(
                    "Class does not inherit from any base class",
                    ValidationSeverity.WARNING,
                    f"{name}.{main_class.name}"
                )
                
        except Exception as e:
            result.add_failure(
                f"Structure validation error: {e}",
                ValidationSeverity.ERROR,
                name
            )
            
        return result
        
    async def validate_contracts(self, code: str, name: str) -> ValidationResult:
        """Validate component contracts (type hints, return values).
        
        Args:
            code: Source code to validate
            name: Component name
            
        Returns:
            ValidationResult with contract validation outcome
        """
        result = ValidationResult(success=True)
        
        try:
            tree = ast.parse(code)
            
            # Check for type hints in method signatures
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Check for return type hint
                    if node.returns is None and node.name not in ["__init__"]:
                        result.add_failure(
                            f"Method {node.name} missing return type hint",
                            ValidationSeverity.INFO,
                            f"{name}.{node.name}"
                        )
                        
                    # Check for parameter type hints
                    for arg in node.args.args:
                        if arg.arg != "self" and arg.annotation is None:
                            result.add_failure(
                                f"Parameter {arg.arg} in {node.name} missing type hint",
                                ValidationSeverity.INFO,
                                f"{name}.{node.name}"
                            )
                            
        except Exception as e:
            result.add_failure(
                f"Contract validation error: {e}",
                ValidationSeverity.ERROR,
                name
            )
            
        return result
        
    async def validate_integration(self, code: str, name: str) -> ValidationResult:
        """Validate integration aspects (imports, dependencies).
        
        Args:
            code: Source code to validate
            name: Component name
            
        Returns:
            ValidationResult with integration validation outcome
        """
        result = ValidationResult(success=True)
        
        try:
            tree = ast.parse(code)
            
            # Check imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    imports.append(node.module or "")
                    
            # Check for required imports
            if "autocoder_cc" not in str(imports):
                result.add_failure(
                    "Component does not import from autocoder_cc",
                    ValidationSeverity.WARNING,
                    name
                )
                
            # Check for dangerous imports
            dangerous_imports = ["os.system", "subprocess", "eval", "exec"]
            for imp in imports:
                if any(danger in imp for danger in dangerous_imports):
                    result.add_failure(
                        f"Potentially dangerous import: {imp}",
                        ValidationSeverity.WARNING,
                        name,
                        {"import": imp}
                    )
                    
        except Exception as e:
            result.add_failure(
                f"Integration validation error: {e}",
                ValidationSeverity.ERROR,
                name
            )
            
        return result
        
    async def validate_system(self, system_config: Dict[str, Any]) -> ValidationResult:
        """Validate an entire system configuration.
        
        Args:
            system_config: System configuration dictionary
            
        Returns:
            ValidationResult with system validation outcome
        """
        result = ValidationResult(success=True)
        
        # Validate components exist
        if "components" not in system_config:
            result.add_failure(
                "System configuration missing 'components' field",
                ValidationSeverity.ERROR,
                "system_config"
            )
            
        # Validate connections
        if "connections" in system_config and "components" in system_config:
            components = set(system_config["components"].keys())
            for conn in system_config.get("connections", []):
                if conn.get("from") not in components:
                    result.add_failure(
                        f"Connection from unknown component: {conn.get('from')}",
                        ValidationSeverity.ERROR,
                        "connections"
                    )
                if conn.get("to") not in components:
                    result.add_failure(
                        f"Connection to unknown component: {conn.get('to')}",
                        ValidationSeverity.ERROR,
                        "connections"
                    )
                    
        return result