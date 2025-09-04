"""Analyze blueprints to identify RPC patterns for migration."""
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
import json
from dataclasses import dataclass
from autocoder_cc.observability import get_logger
from tests.contracts.blueprint_structure_contract import BlueprintContract

@dataclass
class RPCPattern:
    """Detected RPC pattern in blueprint."""
    component_name: str
    pattern_type: str  # 'rpc_call', 'direct_reference', 'synchronous_wait'
    location: str  # Line or section in blueprint
    details: Dict[str, Any]
    migration_hint: str

class BlueprintAnalyzer:
    """Analyzes blueprints for RPC patterns that need migration."""
    
    def __init__(self):
        self.logger = get_logger("BlueprintAnalyzer")
        self.rpc_patterns = []
        
    def analyze_blueprint(self, blueprint_path: Path) -> List[RPCPattern]:
        """Analyze a blueprint file for RPC patterns."""
        self.logger.info(f"Analyzing blueprint: {blueprint_path}")
        
        # Load blueprint
        with open(blueprint_path, 'r') as f:
            if blueprint_path.suffix == '.yaml':
                blueprint = yaml.safe_load(f)
            else:
                blueprint = json.load(f)
        
        patterns = []
        
        # Check for RPC indicators
        patterns.extend(self._check_rpc_calls(blueprint))
        patterns.extend(self._check_direct_references(blueprint))
        patterns.extend(self._check_synchronous_patterns(blueprint))
        patterns.extend(self._check_bindings(blueprint))
        
        self.logger.info(f"Found {len(patterns)} RPC patterns")
        return patterns
    
    def _check_rpc_calls(self, blueprint: Dict) -> List[RPCPattern]:
        """Check for explicit RPC call patterns."""
        patterns = []
        
        for component in BlueprintContract.get_components(blueprint):
            # Look for RPC-style method calls
            if 'methods' in component:
                for method in component['methods']:
                    if any(keyword in method for keyword in ['call', 'invoke', 'request']):
                        patterns.append(RPCPattern(
                            component_name=component['name'],
                            pattern_type='rpc_call',
                            location=f"component.{component['name']}.methods.{method}",
                            details={'method': method},
                            migration_hint="Convert to message passing through ports"
                        ))
                        
            # Check configuration for RPC endpoints
            config = component.get('config', {})
            if any(key in config for key in ['endpoint', 'service_url', 'rpc_address']):
                patterns.append(RPCPattern(
                    component_name=component['name'],
                    pattern_type='rpc_endpoint',
                    location=f"component.{component['name']}.config",
                    details={'config': config},
                    migration_hint="Replace with port connections"
                ))
        
        return patterns
    
    def _check_direct_references(self, blueprint: Dict) -> List[RPCPattern]:
        """Check for direct component references."""
        patterns = []
        
        for component in BlueprintContract.get_components(blueprint):
            # Check for references to other components
            for field in ['inputs', 'outputs', 'dependencies']:
                if field in component:
                    refs = component[field]
                    if isinstance(refs, list):
                        for ref in refs:
                            if isinstance(ref, str) and '.' in ref:
                                # Likely a direct reference like "other_component.method"
                                patterns.append(RPCPattern(
                                    component_name=component['name'],
                                    pattern_type='direct_reference',
                                    location=f"component.{component['name']}.{field}",
                                    details={'reference': ref},
                                    migration_hint="Use port connections instead of direct references"
                                ))
        
        return patterns
    
    def _check_synchronous_patterns(self, blueprint: Dict) -> List[RPCPattern]:
        """Check for synchronous wait patterns."""
        patterns = []
        
        for component in BlueprintContract.get_components(blueprint):
            # Look for synchronous indicators
            if component.get('type') in ['SynchronousProcessor', 'BlockingHandler']:
                patterns.append(RPCPattern(
                    component_name=component['name'],
                    pattern_type='synchronous_wait',
                    location=f"component.{component['name']}.type",
                    details={'type': component['type']},
                    migration_hint="Convert to async message processing"
                ))
        
        return patterns
    
    def _check_bindings(self, blueprint: Dict) -> List[RPCPattern]:
        """Check binding patterns for RPC-style connections."""
        patterns = []
        
        bindings = blueprint.get('bindings', [])
        for binding in bindings:
            # Old RPC-style bindings might use method calls
            if 'method' in binding or 'function' in binding:
                patterns.append(RPCPattern(
                    component_name=binding.get('source', 'unknown'),
                    pattern_type='rpc_binding',
                    location=f"bindings[{bindings.index(binding)}]",
                    details={'binding': binding},
                    migration_hint="Convert to port-based bindings"
                ))
        
        return patterns
    
    def generate_report(self, patterns: List[RPCPattern]) -> str:
        """Generate migration report."""
        report = ["# Blueprint Migration Analysis Report\n"]
        report.append(f"Found {len(patterns)} RPC patterns to migrate\n\n")
        
        by_type = {}
        for pattern in patterns:
            by_type.setdefault(pattern.pattern_type, []).append(pattern)
        
        for pattern_type, items in by_type.items():
            report.append(f"## {pattern_type.replace('_', ' ').title()} ({len(items)} found)\n")
            for item in items:
                report.append(f"- **{item.component_name}** at {item.location}")
                report.append(f"  - Details: {item.details}")
                report.append(f"  - Migration: {item.migration_hint}\n")
        
        return '\n'.join(report)