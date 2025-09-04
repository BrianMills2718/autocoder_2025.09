#!/usr/bin/env python3
"""
TDD Tests for Deployment Module Extraction

Tests for extracting deployment and environment logic from the monolithic system_generator.py
into clean, modular components for deployment orchestration.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from autocoder_cc.deployment.deployment_manager import DeploymentManager, DeploymentError
from autocoder_cc.deployment.environment_provisioner import EnvironmentProvisioner
from autocoder_cc.blueprint_language.system_blueprint_parser import (
    ParsedSystemBlueprint, ParsedSystem
)


class TestDeploymentManager:
    """Test DeploymentManager extraction from monolith"""
    
    def test_deployment_manager_initialization(self):
        """RED: Test that DeploymentManager can be initialized"""
        # This should fail initially because DeploymentManager doesn't exist
        resource_orchestrator = Mock()
        config_manager = Mock()
        environment_provisioner = Mock()
        
        manager = DeploymentManager(
            resource_orchestrator=resource_orchestrator,
            config_manager=config_manager,
            environment_provisioner=environment_provisioner
        )
        
        assert manager is not None
        assert manager.resource_orchestrator == resource_orchestrator
        assert manager.config_manager == config_manager
        assert manager.environment_provisioner == environment_provisioner
    
    def test_deploy_system(self):
        """RED: Test basic system deployment"""
        mock_env_provisioner = Mock()
        mock_env_config = Mock(
            environment="development",
            debug_enabled=True,
            ssl_enabled=False,
            resource_limits=None,
            database_config={},
            config_map={},
            secrets=[]
        )
        mock_env_provisioner.provision_environment.return_value = mock_env_config
        
        manager = DeploymentManager(Mock(), Mock(), mock_env_provisioner)
        
        blueprint = ParsedSystemBlueprint(
            system=ParsedSystem(
                name="TestSystem",
                description="Test deployment system",
                version="1.0.0",
                components=[],
                bindings=[]
            ),
            raw_blueprint={},
            policy={}
        )
        
        output_dir = Path("/tmp/test_deployment")
        
        # Deploy system
        deployment = manager.deploy_system(blueprint, output_dir)
        
        # Verify deployment structure
        assert deployment is not None
        assert deployment.system_name == "TestSystem"
        assert deployment.environment is not None
        assert deployment.kubernetes_manifests is not None
        assert deployment.docker_compose is not None
    
    def test_kubernetes_manifest_generation(self):
        """RED: Test Kubernetes manifest generation"""
        mock_env_provisioner = Mock()
        mock_env_provisioner.provision_environment.return_value = Mock(
            environment="development",
            config_map={}
        )
        manager = DeploymentManager(Mock(), Mock(), mock_env_provisioner)
        
        blueprint = ParsedSystemBlueprint(
            system=ParsedSystem(
                name="K8sSystem",
                components=[
                    type('Component', (), {
                        'name': 'api',
                        'type': 'APIEndpoint',
                        'config': {'port': 8080}
                    })(),
                    type('Component', (), {
                        'name': 'db',
                        'type': 'Store',
                        'config': {'database': 'postgres'}
                    })()
                ],
                bindings=[]
            ),
            raw_blueprint={},
            policy={}
        )
        
        # Generate K8s manifests
        manifests = manager.generate_kubernetes_manifests(blueprint)
        
        assert "deployment.yaml" in manifests
        assert "service.yaml" in manifests
        assert "configmap.yaml" in manifests
        assert "ingress.yaml" in manifests
        
        # Check deployment has correct containers
        deployment_yaml = manifests["deployment.yaml"]
        assert "api" in deployment_yaml
        assert "db" in deployment_yaml
        assert "8080" in deployment_yaml
    
    def test_docker_compose_generation(self):
        """RED: Test Docker Compose generation"""
        mock_env_provisioner = Mock()
        mock_env_provisioner.provision_environment.return_value = Mock(
            environment="development",
            config_map={}
        )
        manager = DeploymentManager(Mock(), Mock(), mock_env_provisioner)
        
        blueprint = ParsedSystemBlueprint(
            system=ParsedSystem(
                name="DockerSystem",
                components=[
                    type('Component', (), {
                        'name': 'web',
                        'type': 'APIEndpoint',
                        'config': {'port': 3000}
                    })(),
                    type('Component', (), {
                        'name': 'redis',
                        'type': 'Store',
                        'config': {'type': 'redis'}
                    })()
                ],
                bindings=[]
            ),
            raw_blueprint={},
            policy={}
        )
        
        # Generate Docker Compose
        compose = manager.generate_docker_compose(blueprint)
        
        assert compose is not None
        assert "version:" in compose
        assert "services:" in compose
        assert "web:" in compose
        assert "redis:" in compose
        assert "3000:3000" in compose  # Port mapping
    
    def test_resource_allocation_integration(self):
        """RED: Test integration with ResourceOrchestrator"""
        mock_resource_orchestrator = Mock()
        mock_resource_orchestrator.allocate_port.return_value = 8080
        mock_resource_orchestrator.allocate_database.return_value = {
            "type": "postgres",
            "url": "postgresql://localhost:5432/testdb"
        }
        
        mock_env_provisioner = Mock()
        mock_env_provisioner.provision_environment.return_value = Mock(
            environment="development",
            config_map={"TEST": "value"}
        )
        
        manager = DeploymentManager(
            resource_orchestrator=mock_resource_orchestrator,
            config_manager=Mock(),
            environment_provisioner=mock_env_provisioner
        )
        
        blueprint = ParsedSystemBlueprint(
            system=ParsedSystem(
                name="ResourcedSystem",
                components=[
                    type('Component', (), {
                        'name': 'api',
                        'type': 'APIEndpoint',
                        'config': {'port': 8080}
                    })(),
                    type('Component', (), {
                        'name': 'db',
                        'type': 'Store',
                        'config': {'database': 'postgres'}
                    })()
                ],
                bindings=[]
            ),
            raw_blueprint={},
            policy={}
        )
        
        deployment = manager.deploy_system(blueprint, Path("/tmp"))
        
        # Verify resources were allocated
        assert mock_resource_orchestrator.allocate_port.called
        assert mock_resource_orchestrator.allocate_database.called
    
    def test_deployment_validation(self):
        """RED: Test deployment validation and health checks"""
        manager = DeploymentManager(Mock(), Mock(), Mock())
        
        deployment = Mock(
            system_name="TestSystem",
            kubernetes_manifests={"deployment.yaml": "..."},
            health_checks=[
                {"name": "api_health", "endpoint": "/health", "expected": 200},
                {"name": "db_health", "endpoint": "/db/health", "expected": 200}
            ],
            deployed_components=["api", "db"],
            error=None,
            status="deployed"
        )
        
        # Validate deployment
        validation_result = manager.validate_deployment(deployment)
        
        assert validation_result.is_valid
        assert len(validation_result.health_checks) == 2
        # Health checks have component, endpoint, and expected_status
        assert all(hasattr(check, 'component') for check in validation_result.health_checks)
        assert all(hasattr(check, 'endpoint') for check in validation_result.health_checks)
        assert all(check.expected_status == 200 for check in validation_result.health_checks)
    
    def test_environment_specific_deployment(self):
        """RED: Test deployment for different environments"""
        mock_env_provisioner = Mock()
        mock_env_provisioner.provision_environment.side_effect = [
            Mock(environment="development", config_map={"ENV": "dev"}),
            Mock(environment="production", config_map={"ENV": "prod"})
        ]
        manager = DeploymentManager(Mock(), Mock(), mock_env_provisioner)
        
        blueprint = ParsedSystemBlueprint(
            system=ParsedSystem(name="EnvSystem", components=[], bindings=[]),
            raw_blueprint={},
            policy={}
        )
        
        # Deploy to different environments
        dev_deployment = manager.deploy_system(blueprint, Path("/tmp"), environment="development")
        prod_deployment = manager.deploy_system(blueprint, Path("/tmp"), environment="production")
        
        assert dev_deployment.environment == "development"
        assert prod_deployment.environment == "production"
        
        # Production should have different settings
        assert dev_deployment.replicas == 1
        assert prod_deployment.replicas >= 3
        assert prod_deployment.resource_limits is not None


class TestEnvironmentProvisioner:
    """Test EnvironmentProvisioner for environment setup"""
    
    def test_environment_provisioner_initialization(self):
        """RED: Test EnvironmentProvisioner initialization"""
        config_template_engine = Mock()
        secret_manager = Mock()
        
        provisioner = EnvironmentProvisioner(
            config_template_engine=config_template_engine,
            secret_manager=secret_manager
        )
        
        assert provisioner is not None
        assert provisioner.config_template_engine == config_template_engine
        assert provisioner.secret_manager == secret_manager
    
    def test_provision_development_environment(self):
        """RED: Test development environment provisioning"""
        provisioner = EnvironmentProvisioner(Mock(), Mock())
        
        env_config = provisioner.provision_environment(
            environment="development",
            system_name="DevSystem",
            components=[
                type('Component', (), {
                    'name': 'api',
                    'type': 'APIEndpoint',
                    'config': {'debug': True}
                })(),
                type('Component', (), {
                    'name': 'db',
                    'type': 'Store',
                    'config': {'database': 'test.db'}
                })()
            ]
        )
        
        assert env_config.environment == "development"
        assert env_config.debug_enabled == True
        assert env_config.resource_limits is None  # No limits in dev
        assert len(env_config.database_config) >= 0  # May have database config
    
    def test_provision_production_environment(self):
        """RED: Test production environment provisioning"""
        mock_secret_manager = Mock()
        mock_secret_manager.get_secret.return_value = "prod-secret-key"
        
        provisioner = EnvironmentProvisioner(Mock(), mock_secret_manager)
        
        env_config = provisioner.provision_environment(
            environment="production",
            system_name="ProdSystem",
            components=[
                type('Component', (), {
                    'name': 'api',
                    'type': 'APIEndpoint',
                    'config': {'ssl': True}
                })(),
                type('Component', (), {
                    'name': 'db',
                    'type': 'Store',
                    'config': {'database': 'prod'}
                })()
            ]
        )
        
        assert env_config.environment == "production"
        assert env_config.debug_enabled == False
        assert env_config.ssl_enabled == True
        assert env_config.resource_limits is not None
        assert mock_secret_manager.create_secret.called
    
    def test_configuration_injection(self):
        """RED: Test configuration injection for components"""
        mock_template_engine = Mock()
        mock_template_engine.render.return_value = {
            "API_KEY": "${API_KEY}",
            "DB_URL": "postgresql://localhost:5432/mydb",
            "DEBUG": "false"
        }
        
        provisioner = EnvironmentProvisioner(mock_template_engine, Mock())
        
        config = provisioner.inject_configuration(
            component_name="api",
            component_type="APIEndpoint",
            environment="production"
        )
        
        assert "API_KEY" in config
        assert "DB_URL" in config
        assert config["DEBUG"] == "false"
        assert mock_template_engine.render.called
    
    def test_secret_handling(self):
        """RED: Test secret management in deployments"""
        mock_secret_manager = Mock()
        mock_secret_manager.create_secret.return_value = "secret-ref-123"
        
        provisioner = EnvironmentProvisioner(Mock(), mock_secret_manager)
        
        secrets = provisioner.manage_secrets(
            system_name="SecureSystem",
            secrets_required=[
                {"name": "api_key", "type": "api"},
                {"name": "db_password", "type": "database"}
            ],
            environment="production"
        )
        
        assert len(secrets) == 2
        assert all(s.reference for s in secrets)
        assert mock_secret_manager.create_secret.call_count == 2
    
    def test_environment_teardown(self):
        """RED: Test environment cleanup"""
        provisioner = EnvironmentProvisioner(Mock(), Mock())
        
        teardown_result = provisioner.teardown_environment(
            system_name="OldSystem",
            environment="development"
        )
        
        assert teardown_result.success
        assert teardown_result.resources_cleaned > 0
        assert teardown_result.errors == []


class TestDeploymentIntegration:
    """Test integration between deployment components"""
    
    def test_full_deployment_pipeline(self):
        """RED: Test complete deployment pipeline"""
        # Set up mocks
        mock_resource_orchestrator = Mock()
        mock_config_manager = Mock()
        mock_environment_provisioner = Mock()
        
        mock_environment_provisioner.provision_environment.return_value = Mock(
            environment="production",
            config_map={"API_KEY": "test-key"},
            secrets=[]
        )
        
        manager = DeploymentManager(
            resource_orchestrator=mock_resource_orchestrator,
            config_manager=mock_config_manager,
            environment_provisioner=mock_environment_provisioner
        )
        
        blueprint = ParsedSystemBlueprint(
            system=ParsedSystem(
                name="FullSystem",
                components=[
                    type('Component', (), {
                        'name': 'frontend',
                        'type': 'APIEndpoint',
                        'config': {}
                    })(),
                    type('Component', (), {
                        'name': 'backend',
                        'type': 'Store',
                        'config': {}
                    })(),
                    type('Component', (), {
                        'name': 'worker',
                        'type': 'Processor',
                        'config': {}
                    })()
                ],
                bindings=[]
            ),
            raw_blueprint={},
            policy={}
        )
        
        # Run full deployment
        deployment = manager.deploy_system(
            blueprint=blueprint,
            output_dir=Path("/tmp/full_deployment"),
            environment="production"
        )
        
        # Verify all components deployed
        assert deployment.deployed_components == ["frontend", "backend", "worker"]
        assert deployment.environment == "production"
        assert deployment.status == "deployed"
        
        # Verify provisioner was called
        assert mock_environment_provisioner.provision_environment.called
    
    def test_deployment_rollback(self):
        """RED: Test deployment rollback on failure"""
        manager = DeploymentManager(Mock(), Mock(), Mock())
        
        # Simulate failed deployment
        failed_deployment = Mock(
            system_name="FailedSystem",
            status="failed",
            error="Component startup failed"
        )
        
        # Rollback
        rollback_result = manager.rollback_deployment(failed_deployment)
        
        assert rollback_result.success
        assert rollback_result.restored_state is not None
        assert rollback_result.cleanup_performed