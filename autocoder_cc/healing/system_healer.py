from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
System-Level Healer for Autocoder v5.0

Handles system integration issues:
- Resource conflicts (ports, names)
- Configuration issues (dev vs prod)
- Integration pattern compliance
- Service discovery and networking
"""

import logging
import yaml
import json
from typing import Dict, Any, List, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, field
import re


@dataclass
class SystemIssue:
    """Represents a system-level issue"""
    issue_type: str
    component: str
    description: str
    severity: str = "error"
    suggested_fix: Optional[str] = None


@dataclass
class SystemHealingResult:
    """Result of system healing operation"""
    success: bool
    issues_found: List[SystemIssue]
    fixes_applied: List[str]
    warnings: List[str] = field(default_factory=list)
    

class SystemHealer:
    """
    Heals system-level integration and configuration issues.
    
    Focuses on:
    - Port allocation conflicts
    - Service naming conflicts
    - Environment-specific configuration
    - Harness integration compliance
    - Resource limits and requests
    """
    
    def __init__(self):
        self.logger = get_logger("SystemHealer")
        self.allocated_ports: Set[int] = set()
        self.allocated_names: Set[str] = set()
        
    def detect_port_conflicts(self, system_config: Dict[str, Any]) -> List[SystemIssue]:
        """
        Detect port allocation conflicts in system configuration.
        
        Args:
            system_config: System configuration dict
            
        Returns:
            List of port conflict issues
        """
        issues = []
        port_usage = {}
        
        # Scan all components for port configurations
        components = system_config.get('components', [])
        for component in components:
            comp_name = component.get('name', 'unknown')
            
            # Check main port
            if 'port' in component:
                port = component['port']
                if port in port_usage:
                    issues.append(SystemIssue(
                        issue_type="port_conflict",
                        component=comp_name,
                        description=f"Port {port} already used by {port_usage[port]}",
                        suggested_fix=f"Change port to {self._find_free_port(port_usage.keys())}"
                    ))
                else:
                    port_usage[port] = comp_name
            
            # Check additional ports (metrics, health, etc.)
            for key in ['metrics_port', 'health_port', 'admin_port']:
                if key in component:
                    port = component[key]
                    if port in port_usage:
                        issues.append(SystemIssue(
                            issue_type="port_conflict",
                            component=comp_name,
                            description=f"{key} {port} already used by {port_usage[port]}",
                            suggested_fix=f"Change {key} to {self._find_free_port(port_usage.keys())}"
                        ))
                    else:
                        port_usage[port] = f"{comp_name}_{key}"
        
        return issues
    
    def detect_naming_conflicts(self, system_config: Dict[str, Any]) -> List[SystemIssue]:
        """
        Detect service naming conflicts.
        
        Args:
            system_config: System configuration dict
            
        Returns:
            List of naming conflict issues
        """
        issues = []
        names_seen = set()
        
        components = system_config.get('components', [])
        for component in components:
            comp_name = component.get('name', '')
            
            # Check for duplicate names
            if comp_name in names_seen:
                issues.append(SystemIssue(
                    issue_type="naming_conflict",
                    component=comp_name,
                    description=f"Duplicate component name: {comp_name}",
                    suggested_fix=f"Rename to {comp_name}_2 or use more descriptive name"
                ))
            else:
                names_seen.add(comp_name)
            
            # Check for invalid characters in names
            if not re.match(r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$', comp_name):
                issues.append(SystemIssue(
                    issue_type="invalid_name",
                    component=comp_name,
                    description=f"Invalid component name: {comp_name} (must be lowercase alphanumeric)",
                    suggested_fix=comp_name.lower().replace('_', '-')
                ))
        
        return issues
    
    def detect_configuration_issues(self, system_config: Dict[str, Any], 
                                  environment: str = "development") -> List[SystemIssue]:
        """
        Detect environment-specific configuration issues.
        
        Args:
            system_config: System configuration dict
            environment: Target environment (development/production)
            
        Returns:
            List of configuration issues
        """
        issues = []
        
        # Check for hardcoded localhost references in production
        if environment == "production":
            config_str = json.dumps(system_config)
            if "localhost" in config_str or "127.0.0.1" in config_str:
                issues.append(SystemIssue(
                    issue_type="hardcoded_localhost",
                    component="system",
                    description="Hardcoded localhost references found in production config",
                    severity="error",
                    suggested_fix="Use service discovery names or environment variables"
                ))
        
        # Check for missing resource limits in production
        if environment == "production":
            components = system_config.get('components', [])
            for component in components:
                comp_name = component.get('name', 'unknown')
                resources = component.get('resources', {})
                
                if 'limits' not in resources:
                    issues.append(SystemIssue(
                        issue_type="missing_resource_limits",
                        component=comp_name,
                        description=f"Missing resource limits for production deployment",
                        severity="warning",
                        suggested_fix="Add CPU and memory limits"
                    ))
                
                if 'requests' not in resources:
                    issues.append(SystemIssue(
                        issue_type="missing_resource_requests",
                        component=comp_name,
                        description=f"Missing resource requests for production deployment",
                        severity="warning",
                        suggested_fix="Add CPU and memory requests"
                    ))
        
        return issues
    
    def detect_harness_compliance_issues(self, component_code: str, 
                                       component_name: str) -> List[SystemIssue]:
        """
        Detect SystemExecutionHarness integration pattern violations.
        
        Args:
            component_code: Component Python code
            component_name: Name of the component
            
        Returns:
            List of harness compliance issues
        """
        issues = []
        
        # Check for proper stream usage
        if "self.receive_streams" not in component_code and "Source" not in component_code:
            issues.append(SystemIssue(
                issue_type="missing_stream_usage",
                component=component_name,
                description="Component doesn't use receive_streams pattern",
                suggested_fix="Use 'async for item in self.receive_streams[input_name]:'"
            ))
        
        if "self.send_streams" not in component_code and "Sink" not in component_code:
            issues.append(SystemIssue(
                issue_type="missing_stream_usage",
                component=component_name,
                description="Component doesn't use send_streams pattern",
                suggested_fix="Use 'await self.send_streams[output_name].send(data)'"
            ))
        
        # Check for proper async patterns
        if "async def process" not in component_code:
            issues.append(SystemIssue(
                issue_type="missing_async_process",
                component=component_name,
                description="Component missing async process method",
                suggested_fix="Define 'async def process(self):' method"
            ))
        
        return issues
    
    def heal_port_conflicts(self, system_config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Automatically fix port conflicts.
        
        Args:
            system_config: System configuration dict
            
        Returns:
            Tuple of (healed_config, fixes_applied)
        """
        fixes = []
        used_ports = set()
        base_port = 8000
        
        # First pass: collect all used ports
        components = system_config.get('components', [])
        for component in components:
            if 'port' in component:
                used_ports.add(component['port'])
            for key in ['metrics_port', 'health_port', 'admin_port']:
                if key in component:
                    used_ports.add(component[key])
        
        # Second pass: fix conflicts
        seen_ports = set()
        for component in components:
            comp_name = component.get('name', 'unknown')
            
            # Fix main port
            if 'port' in component:
                if component['port'] in seen_ports:
                    new_port = self._find_free_port(seen_ports, base_port)
                    fixes.append(f"Changed {comp_name} port from {component['port']} to {new_port}")
                    component['port'] = new_port
                seen_ports.add(component['port'])
            
            # Fix additional ports
            for key in ['metrics_port', 'health_port', 'admin_port']:
                if key in component:
                    if component[key] in seen_ports:
                        new_port = self._find_free_port(seen_ports, base_port + 1000)
                        fixes.append(f"Changed {comp_name} {key} from {component[key]} to {new_port}")
                        component[key] = new_port
                    seen_ports.add(component[key])
        
        return system_config, fixes
    
    def heal_naming_conflicts(self, system_config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Automatically fix naming conflicts.
        
        Args:
            system_config: System configuration dict
            
        Returns:
            Tuple of (healed_config, fixes_applied)
        """
        fixes = []
        seen_names = set()
        
        components = system_config.get('components', [])
        for component in components:
            original_name = component.get('name', '')
            
            # Fix invalid characters
            clean_name = original_name.lower().replace('_', '-').replace(' ', '-')
            clean_name = re.sub(r'[^a-z0-9-]', '', clean_name)
            
            # Fix duplicates
            if clean_name in seen_names:
                counter = 2
                while f"{clean_name}-{counter}" in seen_names:
                    counter += 1
                clean_name = f"{clean_name}-{counter}"
            
            if clean_name != original_name:
                fixes.append(f"Renamed component '{original_name}' to '{clean_name}'")
                component['name'] = clean_name
                
                # Update references in bindings
                if 'bindings' in system_config:
                    for binding in system_config['bindings']:
                        if binding.get('from', '').startswith(original_name + '.'):
                            binding['from'] = binding['from'].replace(original_name + '.', clean_name + '.')
                        if binding.get('to', '').startswith(original_name + '.'):
                            binding['to'] = binding['to'].replace(original_name + '.', clean_name + '.')
            
            seen_names.add(clean_name)
        
        return system_config, fixes
    
    def heal_configuration_issues(self, system_config: Dict[str, Any], 
                                environment: str = "development") -> Tuple[Dict[str, Any], List[str]]:
        """
        Fix environment-specific configuration issues.
        
        Args:
            system_config: System configuration dict
            environment: Target environment
            
        Returns:
            Tuple of (healed_config, fixes_applied)
        """
        fixes = []
        
        if environment == "production":
            # Replace localhost references
            config_str = json.dumps(system_config)
            if "localhost" in config_str or "127.0.0.1" in config_str:
                config_str = config_str.replace("localhost", "${SERVICE_HOST}")
                config_str = config_str.replace("127.0.0.1", "${SERVICE_HOST}")
                system_config = json.loads(config_str)
                fixes.append("Replaced localhost references with environment variables")
            
            # Add default resource limits
            components = system_config.get('components', [])
            for component in components:
                if 'resources' not in component:
                    component['resources'] = {}
                
                if 'limits' not in component['resources']:
                    component['resources']['limits'] = {
                        'cpu': '1000m',
                        'memory': '512Mi'
                    }
                    fixes.append(f"Added default resource limits to {component['name']}")
                
                if 'requests' not in component['resources']:
                    component['resources']['requests'] = {
                        'cpu': '100m',
                        'memory': '128Mi'
                    }
                    fixes.append(f"Added default resource requests to {component['name']}")
        
        return system_config, fixes
    
    def heal_system(self, system_config: Dict[str, Any], 
                   environment: str = "development") -> SystemHealingResult:
        """
        Detect and heal all system-level issues.
        
        Args:
            system_config: System configuration dict
            environment: Target environment
            
        Returns:
            SystemHealingResult with all fixes applied
        """
        all_issues = []
        all_fixes = []
        
        # Detect all issues
        all_issues.extend(self.detect_port_conflicts(system_config))
        all_issues.extend(self.detect_naming_conflicts(system_config))
        all_issues.extend(self.detect_configuration_issues(system_config, environment))
        
        # Apply fixes
        system_config, port_fixes = self.heal_port_conflicts(system_config)
        all_fixes.extend(port_fixes)
        
        system_config, naming_fixes = self.heal_naming_conflicts(system_config)
        all_fixes.extend(naming_fixes)
        
        system_config, config_fixes = self.heal_configuration_issues(system_config, environment)
        all_fixes.extend(config_fixes)
        
        return SystemHealingResult(
            success=len(all_fixes) > 0,
            issues_found=all_issues,
            fixes_applied=all_fixes,
            warnings=[issue.description for issue in all_issues if issue.severity == "warning"]
        )
    
    def _find_free_port(self, used_ports: Set[int], start_port: int = 8000) -> int:
        """Find next available port number"""
        port = start_port
        while port in used_ports or port in self.allocated_ports:
            port += 1
        self.allocated_ports.add(port)
        return port


def heal_system_configuration(config_path: str, environment: str = "development") -> bool:
    """
    Convenience function to heal a system configuration file.
    
    Args:
        config_path: Path to system configuration file
        environment: Target environment
        
    Returns:
        bool: True if healing was successful
    """
    healer = SystemHealer()
    
    try:
        # Load configuration
        with open(config_path, 'r') as f:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                config = yaml.safe_load(f)
            else:
                config = json.load(f)
        
        # Heal the system
        result = healer.heal_system(config, environment)
        
        if result.success:
            # Backup original
            backup_path = f"{config_path}.backup"
            with open(backup_path, 'w') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    yaml.dump(config, f)
                else:
                    json.dump(config, f, indent=2)
            
            # Write healed configuration
            with open(config_path, 'w') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    yaml.dump(config, f)
                else:
                    json.dump(config, f, indent=2)
            
            logging.info(f"System configuration healed: {config_path}")
            logging.info(f"Fixes applied: {result.fixes_applied}")
            if result.warnings:
                logging.warning(f"Warnings: {result.warnings}")
            
            return True
        
        return False
        
    except Exception as e:
        logging.error(f"Failed to heal system configuration: {e}")
        return False


if __name__ == "__main__":
    # Test the system healer
    test_config = {
        "system": "test_system",
        "components": [
            {
                "name": "API_Gateway",
                "port": 8080,
                "metrics_port": 9090
            },
            {
                "name": "auth-service",
                "port": 8080,  # Conflict!
                "health_port": 9090  # Conflict!
            },
            {
                "name": "data processor",  # Invalid name
                "port": 8082,
                "endpoints": ["/api"]  # Use relative paths instead of hardcoded localhost
            }
        ],
        "environment": "production"
    }
    
    healer = SystemHealer()
    result = healer.heal_system(test_config, "production")
    
    print("Issues found:")
    for issue in result.issues_found:
        print(f"  - [{issue.issue_type}] {issue.component}: {issue.description}")
    
    print("\nFixes applied:")
    for fix in result.fixes_applied:
        print(f"  - {fix}")
    
    print("\nHealed configuration:")
    print(json.dumps(test_config, indent=2))