#!/usr/bin/env python3
"""
Component Manifest System
=========================

Implements dynamic component loading using importlib.
Replaces hardcoded imports with plugin-based architecture.

This implements Step 4 of Enterprise Roadmap v2:
- Components loaded dynamically from manifest
- No hardcoded imports in generated systems
- Plugin-based component discovery
"""
import importlib
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
from dataclasses import dataclass


@dataclass
class ComponentSpec:
    """Specification for a component in the manifest"""
    name: str
    module: str
    class_name: str
    component_type: str
    config: Dict[str, Any]
    dependencies: List[str] = None
    
    def __post_init__(self):
        self.dependencies = self.dependencies or []


class ComponentManifest:
    """Manages component manifest and dynamic loading"""
    
    def __init__(self, manifest_path: Optional[Path] = None):
        self.manifest_path = manifest_path
        self.components: Dict[str, ComponentSpec] = {}
        self.loaded_components: Dict[str, Any] = {}
        self.logger = get_logger(f"{self.__class__.__name__}")
        
        if manifest_path and manifest_path.exists():
            self.load_manifest()
    
    def load_manifest(self):
        """Load components from manifest file"""
        if not self.manifest_path or not self.manifest_path.exists():
            raise FileNotFoundError(f"Component manifest not found: {self.manifest_path}")
        
        try:
            with open(self.manifest_path, 'r') as f:
                manifest_data = yaml.safe_load(f)
            
            self.components.clear()
            
            for component_name, spec_data in manifest_data.get('components', {}).items():
                component_spec = ComponentSpec(
                    name=component_name,
                    module=spec_data['module'],
                    class_name=spec_data['class'],
                    component_type=spec_data['type'],
                    config=spec_data.get('config', {}),
                    dependencies=spec_data.get('dependencies', [])
                )
                self.components[component_name] = component_spec
            
            self.logger.info(f"Loaded {len(self.components)} components from manifest")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load component manifest: {e}")
    
    def save_manifest(self):
        """Save current components to manifest file"""
        if not self.manifest_path:
            raise ValueError("No manifest path specified")
        
        manifest_data = {
            'components': {
                name: {
                    'module': spec.module,
                    'class': spec.class_name,
                    'type': spec.component_type,
                    'config': spec.config,
                    'dependencies': spec.dependencies
                }
                for name, spec in self.components.items()
            }
        }
        
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.manifest_path, 'w') as f:
            yaml.dump(manifest_data, f, default_flow_style=False, sort_keys=True)
        
        self.logger.info(f"Saved manifest with {len(self.components)} components")
    
    def add_component(self, name: str, module: str, class_name: str, 
                     component_type: str, config: Dict[str, Any] = None,
                     dependencies: List[str] = None):
        """Add a component to the manifest"""
        component_spec = ComponentSpec(
            name=name,
            module=module,
            class_name=class_name,
            component_type=component_type,
            config=config or {},
            dependencies=dependencies or []
        )
        self.components[name] = component_spec
        self.logger.info(f"Added component '{name}' to manifest")
    
    def load_component(self, component_name: str) -> Any:
        """Dynamically load a component by name"""
        if component_name in self.loaded_components:
            return self.loaded_components[component_name]
        
        if component_name not in self.components:
            raise ValueError(f"Component '{component_name}' not found in manifest")
        
        spec = self.components[component_name]
        
        try:
            # Load dependencies first
            for dep_name in spec.dependencies:
                if dep_name not in self.loaded_components:
                    self.load_component(dep_name)
            
            # Dynamic import
            self.logger.info(f"Loading component '{component_name}' from module '{spec.module}'")
            module = importlib.import_module(spec.module)
            component_class = getattr(module, spec.class_name)
            
            # Instantiate component
            component_instance = component_class(spec.name, spec.config)
            self.loaded_components[component_name] = component_instance
            
            self.logger.info(f"Successfully loaded component '{component_name}'")
            return component_instance
            
        except ImportError as e:
            raise RuntimeError(f"Failed to import module '{spec.module}' for component '{component_name}': {e}")
        except AttributeError as e:
            raise RuntimeError(f"Class '{spec.class_name}' not found in module '{spec.module}': {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to instantiate component '{component_name}': {e}")
    
    def load_all_components(self) -> Dict[str, Any]:
        """Load all components from manifest"""
        loaded = {}
        
        # Sort components by dependencies (topological sort)
        sorted_components = self._topological_sort()
        
        for component_name in sorted_components:
            component = self.load_component(component_name)
            loaded[component_name] = component
        
        return loaded
    
    def _topological_sort(self) -> List[str]:
        """Sort components by dependencies using topological sort"""
        visited = set()
        temp_visited = set()
        sorted_list = []
        
        def visit(component_name: str):
            if component_name in temp_visited:
                raise RuntimeError(f"Circular dependency detected involving component '{component_name}'")
            if component_name in visited:
                return
            
            temp_visited.add(component_name)
            
            if component_name in self.components:
                for dep in self.components[component_name].dependencies:
                    visit(dep)
            
            temp_visited.remove(component_name)
            visited.add(component_name)
            sorted_list.append(component_name)
        
        for component_name in self.components:
            if component_name not in visited:
                visit(component_name)
        
        return sorted_list
    
    def get_component_info(self, component_name: str) -> Dict[str, Any]:
        """Get information about a component"""
        if component_name not in self.components:
            raise ValueError(f"Component '{component_name}' not found in manifest")
        
        spec = self.components[component_name]
        return {
            'name': spec.name,
            'module': spec.module,
            'class': spec.class_name,
            'type': spec.component_type,
            'config': spec.config,
            'dependencies': spec.dependencies,
            'loaded': component_name in self.loaded_components
        }
    
    def list_components(self) -> List[Dict[str, Any]]:
        """List all components in manifest"""
        return [self.get_component_info(name) for name in self.components]
    
    def clear_loaded_components(self):
        """Clear all loaded component instances"""
        self.loaded_components.clear()
        self.logger.info("Cleared all loaded component instances")


def create_sample_manifest(output_path: Path):
    """Create a sample component manifest for reference"""
    sample_manifest = {
        'components': {
            'user_api': {
                'module': 'components.user_api',
                'class': 'UserAPIComponent',
                'type': 'api_endpoint',
                'config': {
                    'port': 8000,
                    'host': '0.0.0.0'
                },
                'dependencies': []
            },
            'message_source': {
                'module': 'components.message_source',
                'class': 'MessageBusSource',
                'type': 'source',
                'config': {
                    'rabbitmq_url': '${RABBITMQ_URL}',
                    'queue_name': 'events'
                },
                'dependencies': []
            },
            'data_processor': {
                'module': 'components.data_processor',
                'class': 'DataProcessor',
                'type': 'transformer',
                'config': {
                    'batch_size': 100
                },
                'dependencies': ['message_source']
            },
            'data_store': {
                'module': 'components.data_store',
                'class': 'PostgreSQLStore',
                'type': 'store',
                'config': {
                    'database_url': '${DATABASE_URL}'
                },
                'dependencies': ['data_processor']
            }
        }
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(sample_manifest, f, default_flow_style=False, sort_keys=True)
    
    print(f"Sample manifest created at: {output_path}")