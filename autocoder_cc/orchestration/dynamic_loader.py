from autocoder_cc.observability.structured_logging import get_logger
"""
Dynamic Component Loader
Implements plugin-based component loading following Enterprise Roadmap v3.
NO HARDCODED IMPORTS - Components loaded dynamically at runtime.
"""
import importlib
import importlib.util
import inspect
import logging
from pathlib import Path
from typing import Dict, Any, Type, Optional, List
from dataclasses import dataclass
from pydantic import BaseModel, Field, ValidationError
from .component import Component
from autocoder_cc.components.component_registry import component_registry


class ComponentManifestSchema(BaseModel):
    """Pydantic schema for component manifest validation"""
    name: str = Field(..., description="Component name")
    type: str = Field(..., description="Component type")
    module_path: str = Field(..., description="Python module path")
    class_name: str = Field(..., description="Component class name")
    config: Dict[str, Any] = Field(default_factory=dict, description="Component configuration")
    dependencies: List[str] = Field(default_factory=list, description="Component dependencies")


class ManifestSchema(BaseModel):
    """Pydantic schema for entire manifest file"""
    components: List[ComponentManifestSchema] = Field(..., description="List of components")


@dataclass
class ComponentManifest:
    """Component manifest for dynamic loading"""
    name: str
    type: str
    module_path: str
    class_name: str
    config: Dict[str, Any]
    dependencies: List[str]


class DynamicComponentLoader:
    """
    Loads components dynamically based on manifests.
    Replaces hardcoded imports with runtime discovery.
    
    Key principles:
    - No hardcoded imports in generated code
    - Components discovered from manifest
    - Plugin-based architecture
    - Standalone component packages
    """
    
    def __init__(self, base_path: Path = Path("components")):
        self.base_path = base_path
        self.logger = get_logger(self.__class__.__name__)
        self._loaded_modules: Dict[str, Any] = {}
        self._component_classes: Dict[str, Type[Component]] = {}
        
    def load_manifest(self, manifest_path: Path) -> List[ComponentManifest]:
        """Load component manifest from YAML or JSON file with schema validation."""
        import yaml
        
        try:
            with open(manifest_path, 'r') as f:
                manifest_data = yaml.safe_load(f)
            
            # Validate manifest against schema
            validated_manifest = ManifestSchema(**manifest_data)
            
            self.logger.info(f"✅ Manifest schema validation passed for {len(validated_manifest.components)} components")
            
            # Convert to ComponentManifest objects
            components = []
            for comp_data in validated_manifest.components:
                components.append(ComponentManifest(
                    name=comp_data.name,
                    type=comp_data.type,
                    module_path=comp_data.module_path,
                    class_name=comp_data.class_name,
                    config=comp_data.config,
                    dependencies=comp_data.dependencies
                ))
            
            return components
            
        except ValidationError as e:
            self.logger.error(f"❌ Manifest schema validation failed: {e}")
            raise ValueError(f"Invalid manifest schema: {e}")
        except Exception as e:
            self.logger.error(f"❌ Failed to load manifest: {e}")
            raise
    
    def load_component_class(self, manifest: ComponentManifest) -> Type[Component]:
        """Dynamically load a component class from manifest."""
        # Check cache first
        cache_key = f"{manifest.module_path}.{manifest.class_name}"
        if cache_key in self._component_classes:
            return self._component_classes[cache_key]
        
        try:
            # Resolve module path
            if manifest.module_path.startswith('.'):
                # Relative import from components directory
                module_path = self.base_path / manifest.module_path.lstrip('.').replace('.', '/')
                module_path = module_path.with_suffix('.py')
            else:
                # Absolute module path
                module_path = Path(manifest.module_path)
            
            # Load module dynamically
            module = self._load_module_from_path(str(module_path), manifest.name)
            
            # Get the component class
            component_class = getattr(module, manifest.class_name)
            
            # Validate it's a Component subclass
            if not issubclass(component_class, Component):
                raise ValueError(
                    f"Class {manifest.class_name} in {manifest.module_path} "
                    f"is not a subclass of Component"
                )
            
            # Cache for future use
            self._component_classes[cache_key] = component_class
            
            self.logger.info(f"Loaded component class: {manifest.class_name} from {manifest.module_path}")
            return component_class
            
        except Exception as e:
            self.logger.error(f"Failed to load component {manifest.name}: {e}")
            raise
    
    def create_component(self, manifest: ComponentManifest) -> Component:
        """Create component instance with proper naming and readiness methods."""
        import os
        
        try:
            # Determine the actual file path
            if manifest.module_path.startswith('components.'):
                # Convert "components.todo_api_endpoint" to "components/todo_api_endpoint.py"
                file_path = manifest.module_path.replace('.', '/') + '.py'
            elif manifest.module_path.endswith('.py'):
                # It's already a file path - make it relative to base_path
                file_path = self.base_path / manifest.module_path
            else:
                # Assume it's a relative path without extension
                file_path = self.base_path / (manifest.module_path + '.py')
            
            # Make sure we have an absolute path
            if not Path(file_path).is_absolute():
                file_path = Path.cwd() / file_path
            
            # Enhanced file validation
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Component file not found: {file_path}")
            
            if not os.access(file_path, os.R_OK):
                raise PermissionError(f"Component file not readable: {file_path}")
            
            # Load the module
            spec = importlib.util.spec_from_file_location(manifest.name, str(file_path))
            if not spec or not spec.loader:
                raise ImportError(f"Could not load spec for {file_path}")
            
            module = importlib.util.module_from_spec(spec)
            
            # Enhanced module execution with better error handling
            try:
                spec.loader.exec_module(module)
            except Exception as e:
                raise ImportError(f"Failed to execute module {file_path}: {e}")
            
            # Find the component class
            component_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    attr_name.startswith('Generated') and
                    hasattr(attr, '__init__')):
                    component_class = attr
                    break
            
            if not component_class:
                raise RuntimeError(f"No Generated component class found in {manifest.module_path}")
            
            # Create instance with manifest name (not class name)
            try:
                component = component_class(manifest.name, manifest.config)
            except Exception as e:
                raise RuntimeError(f"Failed to instantiate component {manifest.name}: {e}")
            
            # Ensure component has required methods
            if not hasattr(component, 'is_ready'):
                # Add default is_ready implementation
                async def default_is_ready():
                    return True
                component.is_ready = default_is_ready
            
            if not hasattr(component, 'health_check'):
                # Add default health_check implementation
                async def default_health_check():
                    return {
                        "status": "healthy",
                        "component": component_class.__name__,
                        "name": manifest.name
                    }
                component.health_check = default_health_check
            
            self.logger.info(f"✅ Created component: {manifest.name} using class {component_class.__name__}")
            return component
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create component {manifest.name}: {e}")
            raise RuntimeError(f"Failed to create component {manifest.name}: {e}") from e
    
    def load_all_components(self, manifest_path: Path) -> Dict[str, Component]:
        """Load all components from a manifest file."""
        manifests = self.load_manifest(manifest_path)
        components = {}
        
        # Sort by dependencies (simple topological sort)
        sorted_manifests = self._sort_by_dependencies(manifests)
        
        for manifest in sorted_manifests:
            try:
                component = self.create_component(manifest)
                components[manifest.name] = component
            except Exception as e:
                self.logger.error(f"Failed to load component {manifest.name}: {e}")
                # Continue loading other components
                
        return components
    
    def _load_module_from_path(self, module_path: str, module_name: str) -> Any:
        """Load a Python module from file path."""
        # Check cache
        if module_path in self._loaded_modules:
            return self._loaded_modules[module_path]
        
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {module_path}")
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Cache the module
        self._loaded_modules[module_path] = module
        
        return module
    
    def _sort_by_dependencies(self, manifests: List[ComponentManifest]) -> List[ComponentManifest]:
        """Simple topological sort by dependencies."""
        # Create dependency graph
        graph = {m.name: m.dependencies for m in manifests}
        manifest_map = {m.name: m for m in manifests}
        
        # Find components with no dependencies
        sorted_names = []
        remaining = set(graph.keys())
        
        while remaining:
            # Find nodes with no dependencies in remaining set
            no_deps = [
                name for name in remaining
                if not any(dep in remaining for dep in graph[name])
            ]
            
            if not no_deps:
                # Circular dependency - just add remaining
                self.logger.warning(f"Circular dependencies detected: {remaining}")
                no_deps = list(remaining)
            
            sorted_names.extend(sorted(no_deps))
            remaining -= set(no_deps)
        
        return [manifest_map[name] for name in sorted_names]
    
    def discover_components(self, search_path: Optional[Path] = None) -> List[ComponentManifest]:
        """
        Discover components by scanning directory for component files.
        This is an alternative to manifest-based loading.
        """
        search_dir = search_path or self.base_path
        discovered = []
        
        # Look for Python files that might be components
        for py_file in search_dir.rglob("*.py"):
            if py_file.name.startswith('_'):
                continue
                
            try:
                # Load the module to inspect it
                module_name = py_file.stem
                module = self._load_module_from_path(str(py_file), module_name)
                
                # Find Component subclasses
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, Component) and 
                        obj is not Component and
                        not name.startswith('_')):
                        
                        # Create manifest from discovered component
                        manifest = ComponentManifest(
                            name=name.lower(),
                            type=obj.__name__,
                            module_path=str(py_file.relative_to(search_dir)),
                            class_name=name,
                            config={},
                            dependencies=[]
                        )
                        discovered.append(manifest)
                        
                        self.logger.info(f"Discovered component: {name} in {py_file}")
                        
            except Exception as e:
                self.logger.debug(f"Could not inspect {py_file}: {e}")
                continue
                
        return discovered


def create_component_manifest(system_blueprint: Dict[str, Any], output_path: Path) -> None:
    """Create a component manifest file from system blueprint."""
    import yaml
    
    components = []
    for comp in system_blueprint.get('system', {}).get('components', []):
        # Convert blueprint component to manifest format
        manifest_entry = {
            'name': comp['name'],
            'type': comp['type'],
            'module_path': f"./{comp['name']}.py",
            'class_name': f"Generated{comp['type']}_{comp['name']}",
            'config': comp.get('config', {}),
            'dependencies': []  # Could be inferred from bindings
        }
        components.append(manifest_entry)
    
    manifest = {
        'version': '1.0',
        'components': components
    }
    
    with open(output_path, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False)