from typing import Dict, Any, List, Tuple
from autocoder_cc.validation.pipeline_context import PipelineContext, DataFlowPattern
from autocoder_cc.validation.exceptions import ContextBuildException
from tests.contracts.blueprint_structure_contract import BlueprintContract

class PipelineContextBuilder:
    """Builds PipelineContext from blueprint and system information"""
    
    def build_from_blueprint(
        self,
        blueprint: Dict[str, Any],
        component_name: str
    ) -> PipelineContext:
        """Build context from blueprint definition"""
        if not blueprint:
            raise ContextBuildException("Blueprint cannot be empty")
            
        if component_name not in self._get_component_names(blueprint):
            raise ContextBuildException(f"Component {component_name} not found in blueprint")
            
        # Extract system-level information - handle nested structure
        if "system" in blueprint:
            system_info = blueprint["system"]
            system_name = system_info.get("name", "unnamed_system")
            system_description = system_info.get("description", "")
            system_capabilities = system_info.get("capabilities", [])
            deployment = system_info.get("deployment", {})
        else:
            # Flat structure fallback
            system_name = blueprint.get("name", "unnamed_system")
            system_description = blueprint.get("description", "")
            system_capabilities = blueprint.get("capabilities", [])
            deployment = blueprint.get("deployment", {})
        
        context = PipelineContext(
            system_name=system_name,
            system_description=system_description,
            system_capabilities=system_capabilities,
            deployment_target=deployment.get("target", "local"),
            environment=deployment.get("environment", "development")
        )
        
        # Find component and extract its information
        component = self._find_component(blueprint, component_name)
        context.component_name = component_name
        context.component_type = component.get("type", "")
        context.component_role = component.get("role", "")
        context.existing_config = component.get("config", {})
        
        # Extract relationships
        upstream, downstream = self.extract_relationships(blueprint, component_name)
        context.upstream_components = upstream
        context.downstream_components = downstream
        
        # Analyze data flow pattern
        context.data_flow_pattern = self.analyze_data_flow(blueprint)
        
        # Extract data schemas if available
        if "outputs" in component and len(component.get("outputs", [])) > 0:
            context.output_data_schema = component["outputs"][0].get("schema", {})
        if "inputs" in component and len(component.get("inputs", [])) > 0:
            # Would need to look up upstream component's output schema
            pass
        
        # Extract used resources from all components in blueprint
        context.used_resources = self.extract_used_resources(blueprint)
            
        return context
    
    def analyze_data_flow(
        self,
        blueprint: Dict[str, Any]
    ) -> DataFlowPattern:
        """Identify the data flow pattern"""
        # Use BlueprintContract to get components
        components = BlueprintContract.get_components(blueprint)
        component_types = [c.get("type") for c in components]
        
        # Pattern detection logic
        if "Accumulator" in component_types or "Store" in component_types:
            return DataFlowPattern.BATCH
        elif "Source" in component_types and "Sink" in component_types:
            return DataFlowPattern.STREAM
        elif "APIEndpoint" in component_types:
            return DataFlowPattern.API
        elif "WebSocket" in component_types:
            return DataFlowPattern.REALTIME
        else:
            return DataFlowPattern.PIPELINE
    
    def extract_relationships(
        self,
        blueprint: Dict[str, Any],
        component_name: str
    ) -> Tuple[List[Dict], List[Dict]]:
        """Extract upstream and downstream components"""
        upstream = []
        downstream = []
        
        # Use BlueprintContract to get connections and components
        connections = BlueprintContract.get_connections(blueprint)
        components = {c["name"]: c for c in BlueprintContract.get_components(blueprint)}
        
        for connection in connections:
            # Handle both direct dict format and binding string format
            if isinstance(connection, dict):
                # Check if it's a proper connection dict with from/to keys
                if "from" in connection and "to" in connection:
                    from_comp = connection["from"].split(".")[0]
                    to_comp = connection["to"].split(".")[0]
                else:
                    # Skip malformed connections
                    continue
            else:
                # Skip non-dict connections
                continue
            
            if to_comp == component_name and from_comp in components:
                upstream.append({
                    "name": from_comp,
                    "type": components[from_comp].get("type", "")
                })
            elif from_comp == component_name and to_comp in components:
                downstream.append({
                    "name": to_comp,
                    "type": components[to_comp].get("type", "")
                })
                
        return upstream, downstream
    
    def _get_component_names(self, blueprint: Dict[str, Any]) -> List[str]:
        """Extract all component names from blueprint"""
        # Use BlueprintContract to get components
        components = BlueprintContract.get_components(blueprint)
        return [c["name"] for c in components]
    
    def _find_component(self, blueprint: Dict[str, Any], name: str) -> Dict[str, Any]:
        """Find a specific component in blueprint"""
        # Use BlueprintContract to find component
        component = BlueprintContract.find_component(blueprint, name)
        if component is None:
            raise ContextBuildException(f"Component {name} not found")
        return component
    
    def extract_used_resources(self, blueprint: Dict[str, Any]) -> Dict[str, set]:
        """Extract all used resources from components in blueprint"""
        resources = {
            "ports": set(),
            "database_urls": set(),
            "file_paths": set(),
            "api_paths": set(),
            "queue_names": set(),
            "topic_names": set(),
            "environment_variables": set()
        }
        
        # Get all components using BlueprintContract
        components = BlueprintContract.get_components(blueprint)
        
        for component in components:
            config = component.get('config', {})
            
            # Extract ports
            if 'port' in config:
                resources['ports'].add(config['port'])
            if 'ports' in config:
                if isinstance(config['ports'], list):
                    resources['ports'].update(config['ports'])
                else:
                    resources['ports'].add(config['ports'])
            
            # Extract database URLs
            for db_key in ['database_url', 'db_url', 'connection_string', 'postgres_url', 'mysql_url']:
                if db_key in config:
                    resources['database_urls'].add(config[db_key])
            
            # Extract file paths
            for file_key in ['file_path', 'input_path', 'output_path', 'log_path', 'data_file', 'output_file']:
                if file_key in config:
                    resources['file_paths'].add(config[file_key])
            
            # Extract API paths
            for api_key in ['base_path', 'api_path', 'endpoint', 'route']:
                if api_key in config:
                    resources['api_paths'].add(config[api_key])
            
            # Extract queue/topic names
            for queue_key in ['queue_name', 'queue', 'topic_name', 'topic', 'channel']:
                if queue_key in config:
                    if queue_key in ['queue_name', 'queue']:
                        resources['queue_names'].add(config[queue_key])
                    else:
                        resources['topic_names'].add(config[queue_key])
            
            # Extract environment variables
            for env_key in ['env_var', 'environment_variable', 'env_name']:
                if env_key in config:
                    resources['environment_variables'].add(config[env_key])
            
            # Check for environment variables in other config values (e.g., "${VAR_NAME}")
            for key, value in config.items():
                if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                    env_var = value[2:-1]
                    resources['environment_variables'].add(env_var)
        
        return resources