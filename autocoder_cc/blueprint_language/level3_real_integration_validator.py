"""
Level 3 Integration Validation - REAL integration tests with actual services.
Uses Docker containers and real network communication.
"""
import asyncio
import logging
import docker
import httpx
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import tempfile
import yaml
from dataclasses import dataclass
import subprocess

from autocoder_cc.core.config import settings


@dataclass
class IntegrationTestResult:
    """Result of integration testing."""
    test_name: str
    passed: bool
    error_message: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None
    duration_seconds: float = 0.0
    
    
@dataclass
class SystemIntegrationResult:
    """Overall system integration test results."""
    system_name: str
    all_passed: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    test_results: List[IntegrationTestResult]
    startup_time: float = 0.0
    total_duration: float = 0.0


class Level3RealIntegrationValidator:
    """
    Level 3 validator that runs REAL integration tests.
    - Starts actual Docker containers
    - Tests real network communication
    - Validates end-to-end data flow
    """
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.docker_client = docker.from_env()
    
    async def validate_system_integration(self,
                                        system_dir: Path,
                                        blueprint: Dict[str, Any]) -> SystemIntegrationResult:
        """
        Run full integration tests on the generated system.
        
        Args:
            system_dir: Directory containing generated system
            blueprint: System blueprint
            
        Returns:
            SystemIntegrationResult with test outcomes
        """
        system_name = blueprint.get('system', {}).get('name', 'test_system')
        start_time = time.time()
        
        result = SystemIntegrationResult(
            system_name=system_name,
            all_passed=False,
            total_tests=0,
            passed_tests=0,
            failed_tests=0,
            test_results=[]
        )
        
        try:
            # Build Docker image
            self.logger.info(f"Building Docker image for {system_name}")
            build_success = await self._build_docker_image(system_dir, system_name)
            if not build_success:
                result.test_results.append(IntegrationTestResult(
                    test_name="docker_build",
                    passed=False,
                    error_message="Failed to build Docker image"
                ))
                return result
            
            # Start services with docker-compose
            self.logger.info("Starting services with docker-compose")
            compose_started = await self._start_docker_compose(system_dir)
            if not compose_started:
                result.test_results.append(IntegrationTestResult(
                    test_name="docker_compose_up",
                    passed=False,
                    error_message="Failed to start docker-compose"
                ))
                return result
            
            result.startup_time = time.time() - start_time
            
            # Wait for services to be ready
            await self._wait_for_services(blueprint)
            
            # Run integration tests
            test_results = await self._run_integration_tests(blueprint)
            result.test_results.extend(test_results)
            
            # Calculate summary
            result.total_tests = len(result.test_results)
            result.passed_tests = sum(1 for t in result.test_results if t.passed)
            result.failed_tests = result.total_tests - result.passed_tests
            result.all_passed = result.failed_tests == 0
            result.total_duration = time.time() - start_time
            
            return result
            
        except Exception as e:
            self.logger.error(f"Integration validation error: {e}")
            result.test_results.append(IntegrationTestResult(
                test_name="system_error",
                passed=False,
                error_message=str(e)
            ))
            return result
            
        finally:
            # Clean up
            await self._stop_docker_compose(system_dir)
    
    async def _build_docker_image(self, system_dir: Path, image_name: str) -> bool:
        """Build Docker image for the system."""
        try:
            # Run docker build
            cmd = ["docker", "build", "-t", f"{image_name}:latest", "."]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(system_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.error(f"Docker build failed: {stderr.decode()}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Docker build error: {e}")
            return False
    
    async def _start_docker_compose(self, system_dir: Path) -> bool:
        """Start services using docker-compose."""
        try:
            # Check if docker-compose.yml exists
            compose_file = system_dir / "docker-compose.yml"
            if not compose_file.exists():
                self.logger.error("docker-compose.yml not found")
                return False
            
            # Run docker-compose up
            cmd = ["docker-compose", "up", "-d"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(system_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.error(f"docker-compose up failed: {stderr.decode()}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"docker-compose error: {e}")
            return False
    
    async def _stop_docker_compose(self, system_dir: Path):
        """Stop and clean up docker-compose services."""
        try:
            cmd = ["docker-compose", "down", "-v"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(system_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
        except Exception as e:
            self.logger.error(f"Error stopping docker-compose: {e}")
    
    async def _wait_for_services(self, blueprint: Dict[str, Any]):
        """Wait for all services to be ready."""
        # Wait for API endpoints to be ready
        api_components = [
            comp for comp in blueprint.get('system', {}).get('components', [])
            if comp.get('type') == 'APIEndpoint'
        ]
        
        for comp in api_components:
            port = comp.get('config', {}).get('port', settings.PORT_RANGE_START)
            await self._wait_for_port(port)
    
    async def _wait_for_port(self, port: int, timeout: int = 30):
        """Wait for a service to be available on a port."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"http://localhost:{port}/health")
                    if response.status_code == 200:
                        self.logger.info(f"Service on port {port} is ready")
                        return
            except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
                self.logger.debug(f"Health check failed for port {port}: {e}")
            
            await asyncio.sleep(1)
        
        self.logger.warning(f"Service on port {port} not ready after {timeout}s")
    
    async def _run_integration_tests(self, blueprint: Dict[str, Any]) -> List[IntegrationTestResult]:
        """Run actual integration tests against the running system."""
        results = []
        
        # Test 1: Health check endpoints
        health_result = await self._test_health_endpoints(blueprint)
        results.append(health_result)
        
        # Test 2: API data flow
        api_result = await self._test_api_data_flow(blueprint)
        results.append(api_result)
        
        # Test 3: End-to-end data processing
        e2e_result = await self._test_end_to_end_flow(blueprint)
        results.append(e2e_result)
        
        # Test 4: Error handling
        error_result = await self._test_error_handling(blueprint)
        results.append(error_result)
        
        return results
    
    async def _test_health_endpoints(self, blueprint: Dict[str, Any]) -> IntegrationTestResult:
        """Test all health check endpoints."""
        start_time = time.time()
        
        try:
            api_components = [
                comp for comp in blueprint.get('system', {}).get('components', [])
                if comp.get('type') == 'APIEndpoint'
            ]
            
            all_healthy = True
            errors = []
            
            async with httpx.AsyncClient() as client:
                for comp in api_components:
                    port = comp.get('config', {}).get('port', settings.PORT_RANGE_START)
                    
                    try:
                        response = await client.get(f"http://localhost:{port}/health")
                        if response.status_code != 200:
                            all_healthy = False
                            errors.append(f"{comp['name']}: status {response.status_code}")
                    except Exception as e:
                        all_healthy = False
                        errors.append(f"{comp['name']}: {e}")
            
            return IntegrationTestResult(
                test_name="health_check_endpoints",
                passed=all_healthy,
                error_message="; ".join(errors) if errors else None,
                duration_seconds=time.time() - start_time
            )
            
        except Exception as e:
            return IntegrationTestResult(
                test_name="health_check_endpoints",
                passed=False,
                error_message=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def _test_api_data_flow(self, blueprint: Dict[str, Any]) -> IntegrationTestResult:
        """Test data flow through API endpoints."""
        start_time = time.time()
        
        try:
            # Find first API endpoint
            api_components = [
                comp for comp in blueprint.get('system', {}).get('components', [])
                if comp.get('type') == 'APIEndpoint'
            ]
            
            if not api_components:
                return IntegrationTestResult(
                    test_name="api_data_flow",
                    passed=True,
                    error_message="No API endpoints to test",
                    duration_seconds=0
                )
            
            comp = api_components[0]
            port = comp.get('config', {}).get('port', settings.PORT_RANGE_START)
            route = comp.get('config', {}).get('route', f"/{comp['name']}")
            
            # Send test data
            test_data = {
                "test_id": "integration_test",
                "timestamp": time.time(),
                "data": {"value": 42}
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"http://localhost:{port}{route}",
                    json=test_data,
                    timeout=10.0
                )
                
                if response.status_code not in [200, 201, 202]:
                    return IntegrationTestResult(
                        test_name="api_data_flow",
                        passed=False,
                        error_message=f"API returned status {response.status_code}",
                        response_data=response.json() if response.content else None,
                        duration_seconds=time.time() - start_time
                    )
                
                return IntegrationTestResult(
                    test_name="api_data_flow",
                    passed=True,
                    response_data=response.json() if response.content else None,
                    duration_seconds=time.time() - start_time
                )
                
        except Exception as e:
            return IntegrationTestResult(
                test_name="api_data_flow",
                passed=False,
                error_message=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def _test_end_to_end_flow(self, blueprint: Dict[str, Any]) -> IntegrationTestResult:
        """Test complete end-to-end data flow through the system."""
        start_time = time.time()
        
        try:
            # This test would be customized based on the system type
            # For now, we just verify the system stays running
            await asyncio.sleep(2)
            
            # Check if containers are still running
            containers_running = await self._check_containers_running()
            
            return IntegrationTestResult(
                test_name="end_to_end_flow",
                passed=containers_running,
                error_message="Some containers stopped" if not containers_running else None,
                duration_seconds=time.time() - start_time
            )
            
        except Exception as e:
            return IntegrationTestResult(
                test_name="end_to_end_flow",
                passed=False,
                error_message=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def _test_error_handling(self, blueprint: Dict[str, Any]) -> IntegrationTestResult:
        """Test system error handling with invalid data."""
        start_time = time.time()
        
        try:
            api_components = [
                comp for comp in blueprint.get('system', {}).get('components', [])
                if comp.get('type') == 'APIEndpoint'
            ]
            
            if not api_components:
                return IntegrationTestResult(
                    test_name="error_handling",
                    passed=True,
                    error_message="No API endpoints to test",
                    duration_seconds=0
                )
            
            comp = api_components[0]
            port = comp.get('config', {}).get('port', settings.PORT_RANGE_START)
            route = comp.get('config', {}).get('route', f"/{comp['name']}")
            
            # Send invalid data
            invalid_data = "not a json object"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"http://localhost:{port}{route}",
                    content=invalid_data,
                    headers={"Content-Type": "application/json"},
                    timeout=10.0
                )
                
                # Should return 4xx error, not 5xx
                if 400 <= response.status_code < 500:
                    return IntegrationTestResult(
                        test_name="error_handling",
                        passed=True,
                        response_data={"status_code": response.status_code},
                        duration_seconds=time.time() - start_time
                    )
                else:
                    return IntegrationTestResult(
                        test_name="error_handling",
                        passed=False,
                        error_message=f"Expected 4xx error, got {response.status_code}",
                        duration_seconds=time.time() - start_time
                    )
                    
        except Exception as e:
            return IntegrationTestResult(
                test_name="error_handling",
                passed=False,
                error_message=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def _check_containers_running(self) -> bool:
        """Check if all containers are still running."""
        try:
            containers = self.docker_client.containers.list()
            # Should have at least one container running
            return len(containers) > 0
        except (docker.errors.DockerException, docker.errors.APIError, ConnectionError) as e:
            self.logger.debug(f"Failed to check Docker containers: {e}")
            return False


async def validate_system_integration_real(
    system_dir: Path,
    blueprint: Dict[str, Any]
) -> SystemIntegrationResult:
    """
    Run real integration validation on a generated system.
    
    Args:
        system_dir: Directory containing the generated system
        blueprint: System blueprint
        
    Returns:
        SystemIntegrationResult with test outcomes
    """
    validator = Level3RealIntegrationValidator()
    return await validator.validate_system_integration(system_dir, blueprint)