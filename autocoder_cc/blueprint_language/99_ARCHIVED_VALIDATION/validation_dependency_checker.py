"""
V5.0 ValidationDependencyChecker - Pre-flight dependency validation with fail-hard enforcement
Validates all dependencies are configured before starting validation pipeline
"""

import os
import asyncio
import subprocess
from typing import List, Optional, Dict, Any
import logging
from dataclasses import dataclass

from .validation_result_types import ValidationDependencyError
from autocoder_cc.observability.structured_logging import get_logger


logger = get_logger(__name__)


@dataclass
class DependencyStatus:
    """Status of individual dependency"""
    name: str
    available: bool
    error_message: Optional[str] = None
    version: Optional[str] = None
    connection_test_passed: bool = False


@dataclass
class BehavioralDependency:
    """External service dependency from blueprint component"""
    service_name: str
    service_type: str
    endpoint: Optional[str] = None
    required_for_validation: bool = True


class ValidationDependencyChecker:
    """Pre-flight dependency validation with fail-hard enforcement"""
    
    def __init__(self):
        self.llm_configured = False
        self.database_available = False
        self.external_services = {}
        self.dependency_cache = {}
        
    async def validate_all_dependencies_configured(self, blueprint) -> None:
        """
        Fail hard if any required dependencies are missing
        
        Args:
            blueprint: SystemBlueprint with components and dependencies
            
        Raises:
            ValidationDependencyError: When any required dependency is missing
        """
        missing_deps = []
        
        # Check LLM availability for Level 4 semantic validation
        llm_status = await self._check_llm_configuration()
        if not llm_status.available:
            missing_deps.append(
                f"LLM (OPENAI_API_KEY or ANTHROPIC_API_KEY required for Level 4 semantic validation): {llm_status.error_message}"
            )
        
        # Check database availability for Level 3 integration testing
        db_status = await self._check_database_availability()
        if not db_status.available:
            missing_deps.append(
                f"Database (PostgreSQL required for Level 3 integration testing): {db_status.error_message}"
            )
        
        # Check external services for each component
        external_service_deps = self._extract_external_service_dependencies(blueprint)
        for service_dep in external_service_deps:
            service_status = await self._check_external_service_availability(service_dep)
            if not service_status.available:
                missing_deps.append(
                    f"External service '{service_dep.service_name}' (type: {service_dep.service_type}) "
                    f"required by validation: {service_status.error_message}"
                )
        
        # Check framework dependencies
        framework_deps = await self._check_framework_dependencies()
        for dep_name, dep_status in framework_deps.items():
            if not dep_status.available:
                missing_deps.append(
                    f"Framework dependency '{dep_name}': {dep_status.error_message}"
                )
        
        # Fail hard if any dependencies are missing
        if missing_deps:
            error_message = (
                "Cannot proceed with validation - missing required dependencies:\n" +
                "\n".join(f"  - {dep}" for dep in missing_deps) +
                "\n\nAll dependencies must be configured and available during development."
            )
            logger.error(f"Dependency validation failed: {error_message}")
            raise ValidationDependencyError(error_message)
        
        logger.info("All dependencies validated successfully - proceeding with validation pipeline")
    
    async def _check_llm_configuration(self) -> DependencyStatus:
        """Check if LLM is properly configured and responding"""
        try:
            # Check environment variables
            has_openai = bool(os.environ.get("OPENAI_API_KEY"))
            has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
            
            if not (has_openai or has_anthropic):
                return DependencyStatus(
                    name="LLM",
                    available=False,
                    error_message="Neither OPENAI_API_KEY nor ANTHROPIC_API_KEY environment variables are set"
                )
            
            # Test actual connectivity
            connection_test = await self._test_llm_connectivity(has_openai, has_anthropic)
            
            return DependencyStatus(
                name="LLM",
                available=connection_test["success"],
                error_message=connection_test.get("error"),
                version=connection_test.get("version"),
                connection_test_passed=connection_test["success"]
            )
            
        except Exception as e:
            return DependencyStatus(
                name="LLM",
                available=False,
                error_message=f"LLM configuration check failed: {e}"
            )
    
    async def _test_llm_connectivity(self, has_openai: bool, has_anthropic: bool) -> Dict[str, Any]:
        """Test actual LLM connectivity"""
        try:
            if has_openai:
                # Test OpenAI connectivity
                import openai
                client = openai.OpenAI()
                # Simple test call
                response = await asyncio.to_thread(
                    client.chat.completions.create,
                    model="o3-mini",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=1
                )
                return {
                    "success": True,
                    "provider": "OpenAI",
                    "version": "o3-mini"
                }
            elif has_anthropic:
                # Test Anthropic connectivity
                import anthropic
                client = anthropic.Anthropic()
                # Simple test call
                response = await asyncio.to_thread(
                    client.messages.create,
                    model="claude-3-haiku-20240307",
                    max_tokens=1,
                    messages=[{"role": "user", "content": "test"}]
                )
                return {
                    "success": True,
                    "provider": "Anthropic",
                    "version": "claude-3-haiku-20240307"
                }
        except ImportError as e:
            return {
                "success": False,
                "error": f"Required LLM client library not installed: {e}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"LLM connectivity test failed: {e}"
            }
        
        return {
            "success": False,
            "error": "No LLM provider configured"
        }
    
    async def _check_database_availability(self) -> DependencyStatus:
        """Check if database is available for Level 3 integration testing"""
        try:
            # Check for database URL configuration
            database_url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
            
            if not database_url:
                return DependencyStatus(
                    name="Database",
                    available=False,
                    error_message="DATABASE_URL or POSTGRES_URL environment variable not set"
                )
            
            # Test database connectivity
            db_test = await self._test_database_connectivity(database_url)
            
            return DependencyStatus(
                name="Database",
                available=db_test["success"],
                error_message=db_test.get("error"),
                version=db_test.get("version"),
                connection_test_passed=db_test["success"]
            )
            
        except Exception as e:
            return DependencyStatus(
                name="Database",
                available=False,
                error_message=f"Database availability check failed: {e}"
            )
    
    async def _test_database_connectivity(self, database_url: str) -> Dict[str, Any]:
        """Test actual database connectivity"""
        try:
            # Try to connect using asyncpg (PostgreSQL)
            import asyncpg
            
            # Parse connection details
            conn = await asyncpg.connect(database_url)
            
            # Test basic query
            version = await conn.fetchval("SELECT version()")
            await conn.close()
            
            return {
                "success": True,
                "version": version,
                "connection_type": "PostgreSQL"
            }
            
        except ImportError:
            return {
                "success": False,
                "error": "asyncpg library not installed (required for PostgreSQL connectivity)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Database connectivity test failed: {e}"
            }
    
    def _extract_external_service_dependencies(self, blueprint) -> List[BehavioralDependency]:
        """Extract external service dependencies from blueprint components"""
        external_deps = []
        
        if not hasattr(blueprint, 'components'):
            return external_deps
        
        for component in blueprint.components:
            # Check for behavioral_dependencies
            if hasattr(component, 'behavioral_dependencies') and component.behavioral_dependencies:
                for dep in component.behavioral_dependencies:
                    if hasattr(dep, 'service_name'):
                        external_deps.append(BehavioralDependency(
                            service_name=dep.service_name,
                            service_type=getattr(dep, 'service_type', 'unknown'),
                            endpoint=getattr(dep, 'endpoint', None),
                            required_for_validation=getattr(dep, 'required_for_validation', True)
                        ))
            
            # Check for external API dependencies in component configuration
            if hasattr(component, 'config') and isinstance(component.config, dict):
                api_endpoints = component.config.get('api_endpoints', [])
                for endpoint in api_endpoints:
                    if isinstance(endpoint, dict) and 'url' in endpoint:
                        external_deps.append(BehavioralDependency(
                            service_name=endpoint.get('name', 'unknown_api'),
                            service_type='http_api',
                            endpoint=endpoint['url'],
                            required_for_validation=endpoint.get('required_for_validation', True)
                        ))
        
        return external_deps
    
    async def _check_external_service_availability(self, service_dep: BehavioralDependency) -> DependencyStatus:
        """Check if external service is available"""
        try:
            if service_dep.service_type == 'http_api' and service_dep.endpoint:
                # Test HTTP API connectivity
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(service_dep.endpoint, timeout=5) as response:
                        return DependencyStatus(
                            name=service_dep.service_name,
                            available=response.status < 500,
                            connection_test_passed=response.status < 500,
                            error_message=f"HTTP {response.status}" if response.status >= 500 else None
                        )
            else:
                # For non-HTTP services, assume available if not testable
                # In production, this would include more sophisticated service discovery
                return DependencyStatus(
                    name=service_dep.service_name,
                    available=True,
                    error_message=f"Service type '{service_dep.service_type}' not testable - assuming available"
                )
                
        except ImportError:
            return DependencyStatus(
                name=service_dep.service_name,
                available=False,
                error_message="aiohttp library required for HTTP API dependency testing"
            )
        except Exception as e:
            return DependencyStatus(
                name=service_dep.service_name,
                available=False,
                error_message=f"External service connectivity test failed: {e}"
            )
    
    async def _check_framework_dependencies(self) -> Dict[str, DependencyStatus]:
        """Check framework-level dependencies"""
        framework_deps = {}
        
        # Check Python version
        python_version = await self._check_python_version()
        framework_deps["python"] = python_version
        
        # Check required Python packages
        required_packages = [
            "pydantic", "yaml", "jinja2", "asyncio",
            "dataclasses", "typing_extensions"
        ]
        
        for package in required_packages:
            package_status = await self._check_python_package(package)
            framework_deps[f"package_{package}"] = package_status
        
        return framework_deps
    
    async def _check_python_version(self) -> DependencyStatus:
        """Check Python version compatibility"""
        try:
            import sys
            version = sys.version_info
            
            # Require Python 3.8+
            if version.major >= 3 and version.minor >= 8:
                return DependencyStatus(
                    name="python",
                    available=True,
                    version=f"{version.major}.{version.minor}.{version.micro}"
                )
            else:
                return DependencyStatus(
                    name="python",
                    available=False,
                    error_message=f"Python 3.8+ required, found {version.major}.{version.minor}.{version.micro}"
                )
        except Exception as e:
            return DependencyStatus(
                name="python",
                available=False,
                error_message=f"Python version check failed: {e}"
            )
    
    async def _check_python_package(self, package_name: str) -> DependencyStatus:
        """Check if required Python package is available"""
        try:
            import importlib
            module = importlib.import_module(package_name)
            version = getattr(module, '__version__', 'unknown')
            
            return DependencyStatus(
                name=package_name,
                available=True,
                version=version
            )
        except ImportError:
            return DependencyStatus(
                name=package_name,
                available=False,
                error_message=f"Required package '{package_name}' not installed"
            )
        except Exception as e:
            return DependencyStatus(
                name=package_name,
                available=False,
                error_message=f"Package check failed: {e}"
            )
    
    async def get_dependency_report(self, blueprint) -> Dict[str, Any]:
        """Get comprehensive dependency status report"""
        try:
            # Check all dependencies without failing
            llm_status = await self._check_llm_configuration()
            db_status = await self._check_database_availability()
            framework_deps = await self._check_framework_dependencies()
            
            external_service_deps = self._extract_external_service_dependencies(blueprint)
            external_services = {}
            for service_dep in external_service_deps:
                service_status = await self._check_external_service_availability(service_dep)
                external_services[service_dep.service_name] = service_status
            
            return {
                "llm": llm_status,
                "database": db_status,
                "framework": framework_deps,
                "external_services": external_services,
                "all_available": all([
                    llm_status.available,
                    db_status.available,
                    all(dep.available for dep in framework_deps.values()),
                    all(dep.available for dep in external_services.values())
                ])
            }
            
        except Exception as e:
            return {
                "error": f"Dependency report generation failed: {e}",
                "all_available": False
            }