#!/usr/bin/env python3
"""
System File Manager - Extracted from SystemGenerator
Handles file operations, directory setup, and system assembly
"""
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any
import logging

from .system_blueprint_parser import ParsedSystemBlueprint

logger = logging.getLogger(__name__)


class SystemFileManager:
    """
    Manages file operations for system generation
    Extracted from SystemGenerator to reduce monolith size
    """
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def combine_into_final_system(self, 
                                scaffold_dir: Path, 
                                components: List[Any], 
                                system_blueprint: ParsedSystemBlueprint,
                                deployment_dir: Path) -> Path:
        """
        Combine scaffold and components into final deployable system
        
        Args:
            scaffold_dir: Path to generated scaffold
            components: List of generated components
            system_blueprint: System blueprint
            deployment_dir: Path to deployment artifacts
            
        Returns:
            Path to final system directory
        """
        system_name = system_blueprint.system.name
        final_system_dir = self.output_dir / system_name
        
        logger.info(f"Combining scaffold and components into final system: {final_system_dir}")
        
        # Create final system directory
        final_system_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy scaffold as base
        self._copy_directory_contents(scaffold_dir, final_system_dir)
        
        # Add component files
        self._integrate_components(final_system_dir, components)
        
        # Copy deployment artifacts
        if deployment_dir and deployment_dir.exists():
            self._integrate_deployment_artifacts(final_system_dir, deployment_dir)
        
        # Create additional structure
        self._create_system_structure(final_system_dir, system_blueprint)
        
        # Generate system metadata
        self._generate_system_metadata(final_system_dir, system_blueprint, components)
        
        logger.info(f"✅ Final system created at: {final_system_dir}")
        return final_system_dir
    
    def save_blueprint_with_system(self, system_blueprint: ParsedSystemBlueprint, output_dir: Path) -> None:
        """
        Save the original blueprint alongside the generated system
        
        Args:
            system_blueprint: System blueprint to save
            output_dir: Directory to save blueprint in
        """
        blueprint_file = output_dir / "blueprint.yaml"
        
        # Convert blueprint back to YAML format
        blueprint_data = {
            "schema_version": system_blueprint.schema_version,
            "system": {
                "name": system_blueprint.system.name,
                "description": system_blueprint.system.description,
                "components": []
            },
            "bindings": []
        }
        
        # Add components
        for component in system_blueprint.system.components:
            component_data = {
                "name": component.name,
                "type": component.type,
                "description": component.description,
                "config": component.config
            }
            
            # Add ports if they exist
            if hasattr(component, 'inputs') and component.inputs:
                component_data["inputs"] = [
                    {"name": inp.name, "schema": inp.schema}
                    for inp in component.inputs
                ]
            
            if hasattr(component, 'outputs') and component.outputs:
                component_data["outputs"] = [
                    {"name": out.name, "schema": out.schema}
                    for out in component.outputs
                ]
            
            blueprint_data["system"]["components"].append(component_data)
        
        # Add bindings
        for binding in system_blueprint.system.bindings:
            binding_data = {
                "from": f"{binding.from_component}.{binding.from_port}",
                "to": [f"{to_comp}.{to_port}" 
                       for to_comp, to_port in zip(binding.to_components, binding.to_ports)]
            }
            blueprint_data["bindings"].append(binding_data)
        
        # Write YAML file
        import yaml
        with open(blueprint_file, 'w') as f:
            yaml.dump(blueprint_data, f, default_flow_style=False, indent=2)
        
        logger.info(f"Blueprint saved: {blueprint_file}")
    
    def copy_documentation_generator(self, system_dir: Path):
        """
        Copy documentation generator to the system directory
        
        Args:
            system_dir: Target system directory
        """
        # Create blueprint_language directory
        blueprint_lang_dir = system_dir / "blueprint_language"
        blueprint_lang_dir.mkdir(exist_ok=True)
        
        # Create __init__.py
        init_file = blueprint_lang_dir / "__init__.py"
        init_file.write_text("# Blueprint language module\n")
        
        # Create documentation generator
        doc_gen_file = blueprint_lang_dir / "documentation_generator.py"
        doc_gen_content = '''#!/usr/bin/env python3
"""
Documentation Generator for Generated System
"""

def generate_documentation(system_name: str) -> str:
    """Generate system documentation"""
    return f"""
# {system_name} System Documentation

## Overview
This system was generated automatically by Autocoder4_CC.

## Components
- Auto-discovered from manifest.yaml

## Deployment
- Docker: `docker-compose up`
- Kubernetes: `kubectl apply -f k8s/`

## Monitoring
- Metrics: http://localhost:9090 (Prometheus)
- Health: http://localhost:8080/health
"""

if __name__ == "__main__":
    print(generate_documentation("System"))
'''
        doc_gen_file.write_text(doc_gen_content)
        
        logger.debug(f"Documentation generator copied to: {blueprint_lang_dir}")
    
    def create_init_files(self, system_dir: Path, components: List[Any], system_blueprint: ParsedSystemBlueprint):
        """
        Create __init__.py files throughout the system structure
        
        Args:
            system_dir: System directory
            components: Generated components
            system_blueprint: System blueprint
        """
        # Main __init__.py
        main_init = system_dir / "__init__.py"
        main_init_content = f'''"""
{system_blueprint.system.name} - Generated System
{'=' * (len(system_blueprint.system.name) + 20)}

{system_blueprint.system.description}

Generated by Autocoder4_CC
"""

__version__ = "1.0.0"
__system_name__ = "{system_blueprint.system.name}"
'''
        main_init.write_text(main_init_content)
        
        # Components __init__.py
        components_init = system_dir / "components" / "__init__.py"
        if components_init.parent.exists():
            component_imports = []
            for component in components:
                component_imports.append(f"from .{component.name} import Generated{component.type}_{component.name}")
            
            components_init_content = f'''"""
Generated Components for {system_blueprint.system.name}
"""

# Component imports
{chr(10).join(component_imports) if component_imports else "# No components to import"}

__all__ = [
{chr(10).join([f'    "Generated{comp.type}_{comp.name}",' for comp in components])}
]
'''
            components_init.write_text(components_init_content)
        
        logger.debug("Created __init__.py files")
    
    def update_main_py_imports(self, system_dir: Path, components: List[Any]):
        """
        Update main.py with proper component imports
        
        Args:
            system_dir: System directory
            components: Generated components
        """
        main_py = system_dir / "main.py"
        
        if not main_py.exists():
            logger.warning("main.py not found, skipping import updates")
            return
        
        # Read current content
        content = main_py.read_text()
        
        # Add component imports section if not present
        import_section = "# Dynamic component imports - added by SystemFileManager\n"
        for component in components:
            import_section += f"# from components.{component.name} import Generated{component.type}_{component.name}\n"
        import_section += "# Components are loaded dynamically via manifest.yaml\n\n"
        
        # Insert imports after the existing import section
        lines = content.split('\n')
        import_end_index = 0
        
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                import_end_index = i + 1
        
        # Insert component import comments
        lines.insert(import_end_index, import_section)
        
        # Write updated content
        main_py.write_text('\n'.join(lines))
        
        logger.debug("Updated main.py with component imports")
    
    def setup_autocoder_dependency(self, system_dir: Path):
        """
        Set up autocoder_cc dependency in the generated system
        
        Args:
            system_dir: System directory
        """
        # Create setup.py
        setup_py = system_dir / "setup.py"
        setup_content = '''from setuptools import setup, find_packages

setup(
    name="generated-system",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "autocoder-cc>=1.0.0",
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "prometheus-client>=0.11.0",
        "pydantic>=1.8.0",
        "anyio>=3.6.0",
        "pyyaml>=5.4.0",
    ],
    python_requires=">=3.8",
    author="Autocoder4_CC",
    description="Generated system by Autocoder4_CC",
)
'''
        setup_py.write_text(setup_content)
        
        # Create pyproject.toml
        pyproject_toml = system_dir / "pyproject.toml"
        pyproject_content = '''[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "generated-system"
version = "1.0.0"
description = "Generated system by Autocoder4_CC"
dependencies = [
    "autocoder-cc>=1.0.0",
    "fastapi>=0.68.0",
    "uvicorn>=0.15.0",
    "prometheus-client>=0.11.0",
    "pydantic>=1.8.0",
    "anyio>=3.6.0",
    "pyyaml>=5.4.0",
]
requires-python = ">=3.8"

[tool.setuptools]
packages = ["components", "config"]
'''
        pyproject_toml.write_text(pyproject_content)
        
        logger.debug("Set up Python package structure")
    
    def _copy_directory_contents(self, source_dir: Path, target_dir: Path):
        """Copy all contents from source to target directory"""
        if not source_dir.exists():
            logger.warning(f"Source directory does not exist: {source_dir}")
            return
        
        for item in source_dir.iterdir():
            target_item = target_dir / item.name
            
            if item.is_directory():
                if target_item.exists():
                    shutil.rmtree(target_item)
                shutil.copytree(item, target_item)
            else:
                if target_item.exists():
                    target_item.unlink()
                shutil.copy2(item, target_item)
        
        logger.debug(f"Copied directory contents: {source_dir} -> {target_dir}")
    
    def _integrate_components(self, system_dir: Path, components: List[Any]):
        """Integrate component files into final system"""
        components_dir = system_dir / "components"
        components_dir.mkdir(exist_ok=True)
        
        # Component files should already be in place from scaffold copy
        # This method can be extended for additional component integration logic
        logger.debug(f"Integrated {len(components)} components")
    
    def _integrate_deployment_artifacts(self, system_dir: Path, deployment_dir: Path):
        """Integrate deployment artifacts into final system"""
        # Copy deployment artifacts
        target_deployment_dir = system_dir
        
        for item in deployment_dir.iterdir():
            target_item = target_deployment_dir / item.name
            
            if item.is_directory():
                if target_item.exists():
                    shutil.rmtree(target_item)
                shutil.copytree(item, target_item)
            else:
                if target_item.exists():
                    target_item.unlink()
                shutil.copy2(item, target_item)
        
        logger.debug(f"Integrated deployment artifacts from: {deployment_dir}")
    
    def _create_system_structure(self, system_dir: Path, system_blueprint: ParsedSystemBlueprint):
        """Create additional system structure"""
        # Create tests directory
        tests_dir = system_dir / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        # Create basic test file
        test_file = tests_dir / "test_system.py"
        test_content = f'''"""
Basic tests for {system_blueprint.system.name}
"""
import pytest
import asyncio
from pathlib import Path

def test_system_structure():
    """Test that system has required structure"""
    system_dir = Path(__file__).parent.parent
    
    # Check required files exist
    assert (system_dir / "main.py").exists()
    assert (system_dir / "requirements.txt").exists()
    assert (system_dir / "Dockerfile").exists()
    assert (system_dir / "components").is_dir()

@pytest.mark.asyncio
async def test_system_startup():
    """Test that system can start up"""
    # This would contain actual startup tests
    pass
'''
        test_file.write_text(test_content)
        
        logger.debug("Created additional system structure")
    
    def _generate_system_metadata(self, system_dir: Path, system_blueprint: ParsedSystemBlueprint, components: List[Any]):
        """Generate system metadata file"""
        import json
        from datetime import datetime
        
        metadata = {
            "system_name": system_blueprint.system.name,
            "system_description": system_blueprint.system.description,
            "generated_at": datetime.now().isoformat(),
            "schema_version": system_blueprint.schema_version,
            "generator": "Autocoder4_CC",
            "components": [
                {
                    "name": comp.name,
                    "type": comp.type,
                    "file_path": f"components/{comp.name}.py"
                }
                for comp in components
            ],
            "component_count": len(components),
            "binding_count": len(system_blueprint.system.bindings)
        }
        
        metadata_file = system_dir / "system_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.debug("Generated system metadata")