from autocoder_cc.observability.structured_logging import get_logger
"""
Component Manifest Generator
Generates manifest.yaml for dynamic component loading.
Part of Enterprise Roadmap v3 implementation.
"""
from typing import Dict, Any, List
from pathlib import Path
import yaml


class ManifestGenerator:
    """Generates component manifest files for dynamic loading."""
    
    def generate(self, blueprint: Dict[str, Any]) -> str:
        """Generate manifest.yaml from system blueprint."""
        system = blueprint.get('system', {})
        components = system.get('components', [])
        
        manifest = {
            'version': '1.0',
            'system': system.get('name', 'autocoder-app'),
            'components': []
        }
        
        for comp in components:
            name = comp.get('name', '')
            comp_type = comp.get('type', '')
            config = comp.get('config', {})
            
            # Component entry for manifest
            entry = {
                'name': name,
                'type': comp_type,
                'module_path': f"./{name}.py",
                'class_name': f"Generated{comp_type}_{name}",
                'config': config,
                'dependencies': self._get_dependencies(name, system.get('bindings', []))
            }
            
            manifest['components'].append(entry)
        
        # Add bindings information
        manifest['bindings'] = self._format_bindings(system.get('bindings', []))
        
        return yaml.dump(manifest, default_flow_style=False, sort_keys=False)
    
    def _get_dependencies(self, component_name: str, bindings: List[Dict[str, Any]]) -> List[str]:
        """Extract component dependencies from bindings."""
        deps = []
        
        for binding in bindings:
            target = binding.get('target', {})
            if target.get('component') == component_name:
                source_comp = binding.get('source', {}).get('component')
                if source_comp and source_comp not in deps:
                    deps.append(source_comp)
        
        return deps
    
    def _format_bindings(self, bindings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format bindings for manifest."""
        formatted = []
        
        for binding in bindings:
            source = binding.get('source', {})
            target = binding.get('target', {})
            
            formatted.append({
                'source': f"{source.get('component', '')}.{source.get('stream', '')}",
                'target': f"{target.get('component', '')}.{target.get('stream', '')}"
            })
        
        return formatted
    
    def generate_component_loader(self) -> str:
        """
        Generate a component loader module that provides base classes.
        This allows generated components to work without autocoder framework.
        """
        return '''"""
Component base classes for standalone operation.
This file is generated to make components work without autocoder framework.
"""
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging


class ComponentStatus:
    """Component status tracking."""
    def __init__(self):
        self.messages_processed = 0
        self.errors = 0
        self.is_running = False


class Component(ABC):
    """
    Base component class for standalone operation.
    Minimal implementation to support generated components.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.logger = get_logger(f"Component.{name}")
        
        # Stream connections
        self.send_streams = {}
        self.receive_streams = {}
        
        # Status tracking
        self._status = ComponentStatus()
    
    async def setup(self, context: Optional[Dict[str, Any]] = None) -> None:
        """Setup component."""
        self.logger.info(f"Setting up component: {self.name}")
    
    @abstractmethod
    async def process(self) -> None:
        """Main processing loop - must be implemented by subclasses."""
        pass
    
    async def cleanup(self) -> None:
        """Cleanup component."""
        self.logger.info(f"Cleaning up component: {self.name}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check."""
        return {
            "status": "healthy" if self._status.is_running else "stopped",
            "messages_processed": self._status.messages_processed,
            "errors": self._status.errors
        }


# Re-export common component types
Source = Component
Transformer = Component  
Sink = Component
Store = Component
APIEndpoint = Component
Controller = Component
MetricsEndpoint = Component
Accumulator = Component
'''