"""Migrate RPC blueprints to port-based architecture."""
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
import json
import copy
from autocoder_cc.migration.blueprint_analyzer import BlueprintAnalyzer, RPCPattern
from autocoder_cc.observability import get_logger
from tests.contracts.blueprint_structure_contract import BlueprintContract

class BlueprintMigrator:
    """Migrates RPC-style blueprints to port-based architecture."""
    
    def __init__(self):
        self.logger = get_logger("BlueprintMigrator")
        self.analyzer = BlueprintAnalyzer()
        
    def migrate_blueprint(self, blueprint_path: Path, output_path: Optional[Path] = None) -> Dict:
        """Migrate a blueprint from RPC to port-based."""
        self.logger.info(f"Migrating blueprint: {blueprint_path}")
        
        # Analyze first
        patterns = self.analyzer.analyze_blueprint(blueprint_path)
        self.logger.info(f"Found {len(patterns)} patterns to migrate")
        
        # Load blueprint
        with open(blueprint_path, 'r') as f:
            if blueprint_path.suffix == '.yaml':
                blueprint = yaml.safe_load(f)
            else:
                blueprint = json.load(f)
        
        # Create migrated copy
        migrated = copy.deepcopy(blueprint)
        
        # Apply migrations
        migrated = self._migrate_components(migrated, patterns)
        migrated = self._migrate_bindings(migrated, patterns)
        migrated = self._add_port_definitions(migrated)
        migrated = self._cleanup_rpc_artifacts(migrated)
        
        # Add migration metadata
        migrated['metadata'] = migrated.get('metadata', {})
        migrated['metadata']['migrated_from_rpc'] = True
        migrated['metadata']['migration_version'] = '1.0'
        migrated['metadata']['original_file'] = str(blueprint_path)
        
        # Save if output path provided
        if output_path:
            self._save_blueprint(migrated, output_path)
            self.logger.info(f"Saved migrated blueprint to: {output_path}")
        
        return migrated
    
    def _migrate_components(self, blueprint: Dict, patterns: List[RPCPattern]) -> Dict:
        """Migrate component definitions."""
        for component in BlueprintContract.get_components(blueprint):
            # Remove RPC-specific fields
            component.pop('methods', None)
            component.pop('rpc_endpoints', None)
            
            # Convert synchronous types to async
            if component.get('type') == 'SynchronousProcessor':
                component['type'] = 'Transformer'
            elif component.get('type') == 'BlockingHandler':
                component['type'] = 'Sink'
            
            # Add port definitions if missing
            if 'inputs' not in component and 'outputs' not in component:
                # Infer ports based on component type
                comp_type = component.get('type', 'Transformer')
                
                if comp_type in ['Source', 'Generator']:
                    component['outputs'] = [{'name': 'out', 'schema': 'Any'}]
                elif comp_type in ['Sink', 'Consumer']:
                    component['inputs'] = [{'name': 'in', 'schema': 'Any'}]
                else:  # Transformer, Filter, etc.
                    component['inputs'] = [{'name': 'in', 'schema': 'Any'}]
                    component['outputs'] = [{'name': 'out', 'schema': 'Any'}]
        
        return blueprint
    
    def _migrate_bindings(self, blueprint: Dict, patterns: List[RPCPattern]) -> Dict:
        """Migrate RPC bindings to port connections."""
        new_bindings = []
        
        # Get bindings using proper accessor (handles both structures)
        bindings = blueprint.get('bindings', [])
        if 'system' in blueprint:
            bindings = blueprint.get('system', {}).get('bindings', bindings)
        
        for binding in bindings:
            # Convert RPC-style to port-style
            if 'method' in binding or 'function' in binding:
                # Old style: {source: comp1, target: comp2, method: process}
                # New style: {source: {component: comp1, port: out}, target: {component: comp2, port: in}}
                new_binding = {
                    'source': {
                        'component': binding.get('source'),
                        'port': 'out'  # Default output port
                    },
                    'target': {
                        'component': binding.get('target'),
                        'port': 'in'  # Default input port
                    }
                }
            else:
                # Keep if already port-style
                new_binding = binding
            
            new_bindings.append(new_binding)
        
        # Set bindings in correct location
        if 'system' in blueprint:
            blueprint['system']['bindings'] = new_bindings
        else:
            blueprint['bindings'] = new_bindings
        return blueprint
    
    def _add_port_definitions(self, blueprint: Dict) -> Dict:
        """Ensure all components have port definitions."""
        for component in BlueprintContract.get_components(blueprint):
            # Ensure inputs/outputs are properly formatted
            if 'inputs' in component and isinstance(component['inputs'], list):
                for port in component['inputs']:
                    if isinstance(port, str):
                        # Convert string to proper port definition
                        idx = component['inputs'].index(port)
                        component['inputs'][idx] = {
                            'name': port,
                            'schema': 'Any'
                        }
            
            if 'outputs' in component and isinstance(component['outputs'], list):
                for port in component['outputs']:
                    if isinstance(port, str):
                        idx = component['outputs'].index(port)
                        component['outputs'][idx] = {
                            'name': port,
                            'schema': 'Any'
                        }
        
        return blueprint
    
    def _cleanup_rpc_artifacts(self, blueprint: Dict) -> Dict:
        """Remove RPC-specific artifacts."""
        # Remove RPC-specific top-level fields
        blueprint.pop('rpc_config', None)
        blueprint.pop('service_endpoints', None)
        
        # Clean component configs
        for component in BlueprintContract.get_components(blueprint):
            config = component.get('config', {})
            for rpc_key in ['endpoint', 'service_url', 'rpc_address', 'timeout']:
                config.pop(rpc_key, None)
        
        return blueprint
    
    def _save_blueprint(self, blueprint: Dict, output_path: Path):
        """Save migrated blueprint."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            if output_path.suffix == '.yaml':
                yaml.dump(blueprint, f, default_flow_style=False, sort_keys=False)
            else:
                json.dump(blueprint, f, indent=2)