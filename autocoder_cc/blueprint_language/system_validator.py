#!/usr/bin/env python3
"""
System Validator - Extracted from SystemGenerator
Handles pre-generation and post-generation validation of systems
"""
from typing import List, Dict, Any
from pathlib import Path
import ast
import logging
from dataclasses import dataclass

from .system_blueprint_parser import ParsedSystemBlueprint
from .architectural_validator import ArchitecturalValidator

logger = logging.getLogger(__name__)

@dataclass
class GeneratedSystem:
    """Represents a generated system with all its components"""
    name: str
    scaffold_dir: Path
    deployment_dir: Path
    components: List[Any]
    blueprint: ParsedSystemBlueprint
    metadata: Dict[str, Any]


class SystemValidator:
    """
    Validates system blueprints and generated systems
    Extracted from SystemGenerator to reduce monolith size
    """
    
    def __init__(self):
        self.architectural_validator = ArchitecturalValidator()
    
    def validate_generated_system(self, generated_system: GeneratedSystem) -> List[str]:
        """
        Validate a completely generated system for correctness and completeness
        
        Args:
            generated_system: The generated system to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate system structure
        structure_errors = self._validate_system_structure(generated_system)
        errors.extend(structure_errors)
        
        # Validate component implementations
        component_errors = self._validate_component_implementations(generated_system)
        errors.extend(component_errors)
        
        # Validate configuration files
        config_errors = self._validate_configuration_files(generated_system)
        errors.extend(config_errors)
        
        # Validate deployment artifacts
        deployment_errors = self._validate_deployment_artifacts(generated_system)
        errors.extend(deployment_errors)
        
        return errors
    
    def validate_pre_generation(self, system_blueprint: ParsedSystemBlueprint) -> List[str]:
        """
        Validate system blueprint before generation starts
        
        Args:
            system_blueprint: Parsed blueprint to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Basic blueprint validation
        if not system_blueprint.system.name:
            errors.append("System name is required")
        
        if not system_blueprint.system.components:
            errors.append("System must have at least one component")
        
        # Architectural validation
        arch_errors = self.architectural_validator.validate_system_architecture(system_blueprint)
        for arch_error in arch_errors:
            if arch_error.severity == "error":
                errors.append(f"{arch_error.component}: [{arch_error.error_type}] {arch_error.message}")
        
        # Component validation
        component_errors = self._validate_components(system_blueprint)
        errors.extend(component_errors)
        
        # Binding validation
        binding_errors = self._validate_bindings(system_blueprint)
        errors.extend(binding_errors)
        
        return errors
    
    def _validate_system_structure(self, generated_system: GeneratedSystem) -> List[str]:
        """Validate the structure of a generated system"""
        errors = []
        
        # Check if scaffold directory exists
        if not generated_system.scaffold_dir.exists():
            errors.append(f"Scaffold directory does not exist: {generated_system.scaffold_dir}")
            return errors
        
        # Check for required files
        required_files = [
            "main.py",
            "requirements.txt",
            "Dockerfile",
            "config/system_config.yaml"
        ]
        
        for required_file in required_files:
            file_path = generated_system.scaffold_dir / required_file
            if not file_path.exists():
                errors.append(f"Required file missing: {required_file}")
        
        # Check components directory
        components_dir = generated_system.scaffold_dir / "components"
        if not components_dir.exists():
            errors.append("Components directory missing")
        else:
            # Check for observability module
            if not (components_dir / "observability.py").exists():
                errors.append("Shared observability module missing")
            
            # Check for communication module
            if not (components_dir / "communication.py").exists():
                errors.append("Communication framework missing")
        
        return errors
    
    def _validate_component_implementations(self, generated_system: GeneratedSystem) -> List[str]:
        """Validate individual component implementations"""
        errors = []
        
        components_dir = generated_system.scaffold_dir / "components"
        
        for component in generated_system.components:
            component_file = components_dir / f"{component.name}.py"
            
            if not component_file.exists():
                errors.append(f"Component file missing: {component.name}.py")
                continue
            
            # Validate Python syntax
            try:
                with open(component_file, 'r') as f:
                    content = f.read()
                ast.parse(content)
            except SyntaxError as e:
                errors.append(f"Syntax error in {component.name}.py: {e}")
                continue
            
            # Check for required imports
            if "from autocoder_cc.components.composed_base import ComposedComponent" not in content:
                errors.append(f"Component {component.name} missing ComposedComponent import")
            
            # Check for required class definition
            expected_class = f"Generated{component.type}_{component.name}"
            if f"class {expected_class}" not in content:
                errors.append(f"Component {component.name} missing expected class: {expected_class}")
            
            # Check for process_item method
            if "async def process_item(" not in content:
                errors.append(f"Component {component.name} missing process_item method")
        
        return errors
    
    def _validate_configuration_files(self, generated_system: GeneratedSystem) -> List[str]:
        """Validate configuration files"""
        errors = []
        
        config_dir = generated_system.scaffold_dir / "config"
        
        # Validate system config
        system_config = config_dir / "system_config.yaml"
        if system_config.exists():
            try:
                import yaml
                with open(system_config, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                # Check required sections
                required_sections = ["system", "components", "observability"]
                for section in required_sections:
                    if section not in config_data:
                        errors.append(f"System config missing section: {section}")
            except yaml.YAMLError as e:
                errors.append(f"Invalid YAML in system config: {e}")
        
        return errors
    
    def _validate_deployment_artifacts(self, generated_system: GeneratedSystem) -> List[str]:
        """Validate deployment artifacts"""
        errors = []
        
        # Check Dockerfile
        dockerfile = generated_system.scaffold_dir / "Dockerfile"
        if dockerfile.exists():
            content = dockerfile.read_text()
            
            # Check for required Docker instructions
            required_instructions = ["FROM", "WORKDIR", "COPY", "RUN", "CMD"]
            for instruction in required_instructions:
                if instruction not in content:
                    errors.append(f"Dockerfile missing instruction: {instruction}")
        
        # Check deployment directory if it exists
        if generated_system.deployment_dir and generated_system.deployment_dir.exists():
            # Validate Kubernetes manifests
            k8s_dir = generated_system.deployment_dir / "k8s"
            if k8s_dir.exists():
                required_k8s_files = ["deployment.yaml", "service.yaml"]
                for k8s_file in required_k8s_files:
                    if not (k8s_dir / k8s_file).exists():
                        errors.append(f"Kubernetes manifest missing: {k8s_file}")
        
        return errors
    
    def _validate_components(self, system_blueprint: ParsedSystemBlueprint) -> List[str]:
        """Validate component definitions in blueprint"""
        errors = []
        
        component_names = set()
        
        for component in system_blueprint.system.components:
            # Check for duplicate names
            if component.name in component_names:
                errors.append(f"Duplicate component name: {component.name}")
            component_names.add(component.name)
            
            # Validate component type
            valid_types = [
                "Source", "Transformer", "Filter", "Router", "Aggregator",
                "APIEndpoint", "Controller", "Model", "Store", "Sink"
            ]
            if component.type not in valid_types:
                errors.append(f"Invalid component type '{component.type}' for component '{component.name}'")
            
            # Validate ports
            if hasattr(component, 'inputs'):
                for input_port in component.inputs:
                    if not input_port.name:
                        errors.append(f"Component '{component.name}' has input port without name")
            
            if hasattr(component, 'outputs'):
                for output_port in component.outputs:
                    if not output_port.name:
                        errors.append(f"Component '{component.name}' has output port without name")
        
        return errors
    
    def _validate_bindings(self, system_blueprint: ParsedSystemBlueprint) -> List[str]:
        """Validate component bindings in blueprint"""
        errors = []
        
        component_names = {comp.name for comp in system_blueprint.system.components}
        
        for binding in system_blueprint.system.bindings:
            # Validate source component exists
            if binding.from_component not in component_names:
                errors.append(f"Binding references unknown source component: {binding.from_component}")
            
            # Validate target components exist
            for to_component in binding.to_components:
                if to_component not in component_names:
                    errors.append(f"Binding references unknown target component: {to_component}")
            
            # Validate ports exist (if port information is available)
            # This would require more detailed port validation logic
        
        return errors
    
    def enforce_system_ast_validation(self, system_dir: Path) -> None:
        """
        Enforce AST validation on all Python files in the system
        
        Args:
            system_dir: Directory containing the generated system
        """
        logger.info(f"Enforcing AST validation on system: {system_dir}")
        
        # Find all Python files
        python_files = list(system_dir.rglob("*.py"))
        
        validation_errors = []
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse AST to validate syntax
                ast.parse(content)
                logger.debug(f"✅ AST validation passed: {py_file.relative_to(system_dir)}")
                
            except SyntaxError as e:
                error_msg = f"AST validation failed for {py_file.relative_to(system_dir)}: {e}"
                validation_errors.append(error_msg)
                logger.error(error_msg)
            
            except Exception as e:
                error_msg = f"Unexpected error validating {py_file.relative_to(system_dir)}: {e}"
                validation_errors.append(error_msg)
                logger.error(error_msg)
        
        if validation_errors:
            error_summary = f"AST validation failed for {len(validation_errors)} files:\n" + "\n".join(validation_errors)
            raise ValueError(error_summary)
        
        logger.info(f"✅ AST validation completed successfully for {len(python_files)} Python files")