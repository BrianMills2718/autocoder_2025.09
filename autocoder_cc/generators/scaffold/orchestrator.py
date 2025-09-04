"""
Scaffold Generation Orchestrator - uses plugin architecture.
Follows Enterprise Roadmap v2 Strategy pattern.
"""
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass

from .dockerfile_generator import DockerfileGenerator
from .k8s_generator import K8sManifestGenerator
from .main_generator import MainPyGenerator
from .main_generator_dynamic import DynamicMainPyGenerator
from .structure_generator import StructureGenerator
from .requirements_generator import RequirementsGenerator
from .docker_compose_generator import DockerComposeGenerator
from .manifest_generator import ManifestGenerator


@dataclass
class GeneratedScaffold:
    """Complete generated system scaffold."""
    main_py: str
    dockerfile: str
    requirements_txt: str
    docker_compose: str
    manifest_yaml: Optional[str] = None
    component_loader: Optional[str] = None
    k8s_deployment: Optional[str] = None
    k8s_service: Optional[str] = None
    k8s_configmap: Optional[str] = None
    structure_created: bool = False


class ScaffoldOrchestrator:
    """
    Orchestrates scaffold generation using plugin architecture.
    This replaces the monolithic SystemScaffoldGenerator.
    
    Key principles:
    - Uses strategy pattern with pluggable generators
    - Each generator is independent and focused
    - Configuration comes from centralized settings
    - No hardcoded values
    """
    
    def __init__(self, output_dir: Path, use_dynamic_loading: bool = True):
        self.output_dir = Path(output_dir)
        self.use_dynamic_loading = use_dynamic_loading
        
        # Initialize generator plugins
        self.structure_gen = StructureGenerator(self.output_dir)
        self.dockerfile_gen = DockerfileGenerator()
        self.k8s_gen = K8sManifestGenerator()
        self.main_gen = MainPyGenerator()
        self.dynamic_main_gen = DynamicMainPyGenerator()
        self.requirements_gen = RequirementsGenerator()
        self.docker_compose_gen = DockerComposeGenerator()
        self.manifest_gen = ManifestGenerator()
    
    def generate_scaffold(self, 
                         blueprint: Dict[str, Any], 
                         enable_metrics: bool = True,
                         generate_k8s: bool = False) -> GeneratedScaffold:
        """
        Generate complete system scaffold using plugins.
        
        Args:
            blueprint: Parsed system blueprint
            enable_metrics: Whether to enable Prometheus metrics
            generate_k8s: Whether to generate Kubernetes manifests
            
        Returns:
            GeneratedScaffold with all generated content
        """
        # Create directory structure
        structure_created = self.structure_gen.create_structure(blueprint)
        
        # Generate main.py based on dynamic loading preference
        if self.use_dynamic_loading:
            main_py = self.dynamic_main_gen.generate(blueprint, enable_metrics)
            manifest_yaml = self.manifest_gen.generate(blueprint)
            component_loader = self.manifest_gen.generate_component_loader()
        else:
            main_py = self.main_gen.generate(blueprint, enable_metrics)
            manifest_yaml = None
            component_loader = None
        
        # Generate requirements.txt
        requirements = self.requirements_gen.generate(blueprint, enable_metrics)
        
        # Generate Dockerfile
        dockerfile = self.dockerfile_gen.generate(blueprint)
        
        # Generate docker-compose.yml
        docker_compose = self.docker_compose_gen.generate(blueprint)
        
        # Generate Kubernetes manifests if requested
        k8s_deployment = None
        k8s_service = None
        k8s_configmap = None
        
        if generate_k8s:
            k8s_deployment = self.k8s_gen.generate_deployment(blueprint)
            k8s_service = self.k8s_gen.generate_service(blueprint)
            k8s_configmap = self.k8s_gen.generate_configmap(blueprint)
        
        # Create scaffold object
        scaffold = GeneratedScaffold(
            main_py=main_py,
            dockerfile=dockerfile,
            requirements_txt=requirements,
            docker_compose=docker_compose,
            manifest_yaml=manifest_yaml,
            component_loader=component_loader,
            k8s_deployment=k8s_deployment,
            k8s_service=k8s_service,
            k8s_configmap=k8s_configmap,
            structure_created=structure_created
        )
        
        # Write all files
        self._write_files(blueprint, scaffold)
        
        return scaffold
    
    def _write_files(self, blueprint: Dict[str, Any], scaffold: GeneratedScaffold):
        """Write all generated files to disk."""
        system_name = blueprint.get('system', {}).get('name', 'autocoder-app')
        system_dir = self.output_dir / system_name
        
        # Ensure directory exists
        system_dir.mkdir(parents=True, exist_ok=True)
        
        # Write main files
        (system_dir / "main.py").write_text(scaffold.main_py)
        (system_dir / "Dockerfile").write_text(scaffold.dockerfile)
        (system_dir / "requirements.txt").write_text(scaffold.requirements_txt)
        (system_dir / "docker-compose.yml").write_text(scaffold.docker_compose)
        
        # Write dynamic loading files if enabled
        if scaffold.manifest_yaml:
            components_dir = system_dir / "components"
            components_dir.mkdir(exist_ok=True)
            (components_dir / "manifest.yaml").write_text(scaffold.manifest_yaml)
            
        if scaffold.component_loader:
            (components_dir / "component_base.py").write_text(scaffold.component_loader)
        
        # Write Kubernetes manifests if present
        if scaffold.k8s_deployment:
            k8s_dir = system_dir / "k8s"
            k8s_dir.mkdir(exist_ok=True)
            
            (k8s_dir / "deployment.yaml").write_text(scaffold.k8s_deployment)
            (k8s_dir / "service.yaml").write_text(scaffold.k8s_service)
            (k8s_dir / "configmap.yaml").write_text(scaffold.k8s_configmap)