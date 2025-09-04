#!/usr/bin/env python3
"""
Chaos Engineering Library for AutoCoder4_CC
Production-ready chaos engineering with real failure injection, comprehensive monitoring,
and statistical analysis.

This module contains the core chaos engineering classes that were previously embedded
in the test file. Moving them here establishes a proper library structure and enables
clean imports from scripts and tests.
"""

import asyncio
import subprocess
import sys
import time
import tempfile
import shutil
import json
import signal
import psutil
import docker
import threading
import platform
import statistics
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
import requests
import yaml
import logging
from contextlib import asynccontextmanager
import aiohttp

# Configure structured logging with correlation IDs for production tracing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/chaos_engineering_production.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CorrelationFilter(logging.Filter):
    """Add correlation ID to log records for complete traceability"""
    def filter(self, record):
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = getattr(self, 'correlation_id', 'unknown')
        return True

# Add correlation filter to all handlers
for handler in logger.handlers:
    handler.addFilter(CorrelationFilter())


@dataclass
class InfrastructureComponent:
    """Real infrastructure component for chaos testing"""
    name: str
    component_type: str  # 'rabbitmq', 'kafka', 'consul', 'application'
    container: Optional[object] = None
    container_id: Optional[str] = None
    port: int = 0
    host: str = "localhost"
    health_endpoint: Optional[str] = None
    startup_time: float = 0.0
    is_healthy: bool = False


@dataclass
class ChaosScenario:
    """Chaos engineering scenario definition"""
    name: str
    scenario_type: str  # 'network_partition', 'resource_exhaustion', 'service_failure'
    duration_seconds: int
    target_components: List[str]
    failure_percentage: float  # 0.0 to 1.0
    recovery_time_limit: int
    expected_behavior: str


@dataclass 
class StatisticalMetrics:
    """Statistical analysis of metrics with confidence intervals"""
    mean: float
    median: float
    std_dev: float
    min_value: float
    max_value: float
    percentile_95: float
    percentile_99: float
    sample_size: int
    confidence_interval_95: Tuple[float, float]

@dataclass
class ComprehensiveResilienceMetrics:
    """Comprehensive resilience metrics with statistical analysis"""
    availability_score: float
    availability_stats: StatisticalMetrics
    recovery_time_score: float
    recovery_time_stats: StatisticalMetrics
    error_tolerance_score: float
    error_rate_stats: StatisticalMetrics
    performance_degradation_score: float
    response_time_stats: StatisticalMetrics
    overall_resilience_score: float
    statistical_confidence: float
    measurement_period_seconds: float
    sample_count: int

@dataclass
class ChaosTestResult:
    """Result of a chaos engineering test with comprehensive metrics"""
    scenario: ChaosScenario
    start_time: datetime
    end_time: datetime
    correlation_id: str
    infrastructure_state_before: Dict[str, Any]
    infrastructure_state_after: Dict[str, Any]
    failure_injection_successful: bool
    system_behavior_during_failure: Dict[str, Any]
    recovery_successful: bool
    recovery_time_seconds: float
    measured_resilience_metrics: ComprehensiveResilienceMetrics
    evidence_artifacts: List[str]
    raw_monitoring_data: List[Dict[str, Any]] = field(default_factory=list)
    container_logs_during_failure: Dict[str, str] = field(default_factory=dict)
    network_analysis_data: Dict[str, Any] = field(default_factory=dict)


class RealInfrastructureChaosEngine:
    """Production-grade chaos engineering with comprehensive metrics and monitoring"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.correlation_id = f"chaos_{test_name}_{int(time.time())}"
        self.docker_client = docker.from_env()
        self.infrastructure_components = {}
        self.test_results = []
        self.evidence_dir = Path(f"./chaos_evidence_{test_name}_{int(time.time())}")
        self.evidence_dir.mkdir(exist_ok=True)
        self.networks = {}
        
        # Production monitoring configuration
        self.monitoring_interval = 2.0  # Enhanced monitoring frequency
        self.baseline_duration = 60  # Longer baseline for statistical significance
        self.recovery_timeout = 300  # Extended recovery timeout
        self.sample_size_minimum = 30  # Minimum samples for statistical significance
        
        # Set correlation ID in logger filter
        for handler in logger.handlers:
            for filter_obj in handler.filters:
                if isinstance(filter_obj, CorrelationFilter):
                    filter_obj.correlation_id = self.correlation_id
        
        logger.info(f"Initialized chaos engine: {self.test_name} [correlation_id: {self.correlation_id}]")
        
    async def setup_real_test_infrastructure(self) -> Dict[str, InfrastructureComponent]:
        """Set up actual test infrastructure for chaos engineering"""
        
        logger.info("Setting up real infrastructure for chaos engineering tests")
        
        # Create isolated test network
        test_network = self.docker_client.networks.create(
            f"chaos_test_network_{int(time.time())}",
            driver="bridge",
            attachable=True
        )
        self.networks['test_network'] = test_network
        
        # Start real RabbitMQ cluster
        rabbitmq = await self._start_real_rabbitmq_cluster()
        self.infrastructure_components['rabbitmq'] = rabbitmq
        
        # Start real Kafka cluster
        kafka = await self._start_real_kafka_cluster()
        self.infrastructure_components['kafka'] = kafka
        
        # Start real Consul cluster
        consul = await self._start_real_consul_cluster()
        self.infrastructure_components['consul'] = consul
        
        # Start test application instances
        app_instances = await self._start_test_applications()
        for i, app in enumerate(app_instances):
            self.infrastructure_components[f'app_instance_{i}'] = app
        
        # Wait for all services to be healthy
        await self._wait_for_infrastructure_ready()
        
        # Generate infrastructure evidence
        await self._generate_infrastructure_evidence("setup_complete")
        
        return self.infrastructure_components
    
    async def _start_real_rabbitmq_cluster(self) -> InfrastructureComponent:
        """Start actual RabbitMQ cluster for testing"""
        
        start_time = time.time()
        
        try:
            # Start RabbitMQ container with management plugin
            container = self.docker_client.containers.run(
                "rabbitmq:3-management",
                name=f"chaos_rabbitmq_{int(time.time())}",
                ports={'5672/tcp': None, '15672/tcp': None},
                environment={
                    'RABBITMQ_DEFAULT_USER': 'chaos_user',
                    'RABBITMQ_DEFAULT_PASS': 'chaos_password',
                    'RABBITMQ_VM_MEMORY_HIGH_WATERMARK': '0.8'
                },
                detach=True,
                remove=False,  # Keep for debugging
                network=self.networks['test_network'].name
            )
            
            # Get actual port mappings
            container.reload()
            amqp_port = container.ports['5672/tcp'][0]['HostPort']
            mgmt_port = container.ports['15672/tcp'][0]['HostPort']
            
            component = InfrastructureComponent(
                name="rabbitmq_cluster",
                component_type="rabbitmq",
                container=container,
                container_id=container.id,
                port=int(amqp_port),
                health_endpoint=f"http://localhost:{mgmt_port}/api/aliveness-test/%2F",
                startup_time=time.time() - start_time
            )
            
            # Wait for RabbitMQ to be ready
            await self._wait_for_service_health(component, timeout=60)
            
            logger.info(f"RabbitMQ cluster started: {component.container_id[:12]} on port {component.port}")
            return component
            
        except Exception as e:
            logger.error(f"Failed to start RabbitMQ cluster: {e}")
            raise
    
    async def _start_real_kafka_cluster(self) -> InfrastructureComponent:
        """Start actual Kafka cluster for testing"""
        
        start_time = time.time()
        
        try:
            # Start Zookeeper first
            zk_container = self.docker_client.containers.run(
                "confluentinc/cp-zookeeper:latest",
                name=f"chaos_zookeeper_{int(time.time())}",
                environment={
                    'ZOOKEEPER_CLIENT_PORT': '2181',
                    'ZOOKEEPER_TICK_TIME': '2000'
                },
                detach=True,
                remove=False,
                network=self.networks['test_network'].name
            )
            
            # Wait a bit for Zookeeper
            await asyncio.sleep(5)
            
            # Start Kafka
            kafka_container = self.docker_client.containers.run(
                "confluentinc/cp-kafka:latest",
                name=f"chaos_kafka_{int(time.time())}",
                ports={'9092/tcp': None},
                environment={
                    'KAFKA_BROKER_ID': '1',
                    'KAFKA_ZOOKEEPER_CONNECT': f'{zk_container.name}:2181',
                    'KAFKA_ADVERTISED_LISTENERS': 'PLAINTEXT://localhost:9092',
                    'KAFKA_LISTENERS': 'PLAINTEXT://0.0.0.0:9092',
                    'KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR': '1',
                    'KAFKA_LOG_RETENTION_HOURS': '1'
                },
                detach=True,
                remove=False,
                network=self.networks['test_network'].name
            )
            
            # Get actual port mapping
            kafka_container.reload()
            kafka_port = kafka_container.ports['9092/tcp'][0]['HostPort']
            
            component = InfrastructureComponent(
                name="kafka_cluster",
                component_type="kafka",
                container=kafka_container,
                container_id=kafka_container.id,
                port=int(kafka_port),
                startup_time=time.time() - start_time
            )
            
            # Wait for Kafka to be ready
            await self._wait_for_kafka_ready(component, timeout=90)
            
            logger.info(f"Kafka cluster started: {component.container_id[:12]} on port {component.port}")
            return component
            
        except Exception as e:
            logger.error(f"Failed to start Kafka cluster: {e}")
            raise
    
    async def _start_real_consul_cluster(self) -> InfrastructureComponent:
        """Start actual Consul cluster for testing"""
        
        start_time = time.time()
        
        try:
            # Start Consul container
            container = self.docker_client.containers.run(
                "consul:latest",
                name=f"chaos_consul_{int(time.time())}",
                ports={'8500/tcp': None, '8300/tcp': None},
                environment={
                    'CONSUL_BIND_INTERFACE': 'eth0'
                },
                command='agent -server -bootstrap-expect=1 -ui -client=0.0.0.0',
                detach=True,
                remove=False,
                network=self.networks['test_network'].name
            )
            
            # Get actual port mapping
            container.reload()
            http_port = container.ports['8500/tcp'][0]['HostPort']
            
            component = InfrastructureComponent(
                name="consul_cluster",
                component_type="consul",
                container=container,
                container_id=container.id,
                port=int(http_port),
                health_endpoint=f"http://localhost:{http_port}/v1/status/leader",
                startup_time=time.time() - start_time
            )
            
            # Wait for Consul to be ready
            await self._wait_for_service_health(component, timeout=60)
            
            logger.info(f"Consul cluster started: {component.container_id[:12]} on port {component.port}")
            return component
            
        except Exception as e:
            logger.error(f"Failed to start Consul cluster: {e}")
            raise
    
    async def _start_test_applications(self) -> List[InfrastructureComponent]:
        """Start test application instances"""
        
        applications = []
        
        # Create a simple test application
        app_code = '''
import asyncio
import aiohttp
from aiohttp import web
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def health_check(request):
    return web.json_response({
        "status": "healthy",
        "timestamp": time.time(),
        "instance": "chaos_test_app",
        "uptime": time.time() - app_start_time
    })

async def ready_check(request):
    return web.json_response({
        "status": "ready",
        "timestamp": time.time()
    })

async def stress_endpoint(request):
    # Simulate some processing
    data = await request.json() if request.can_read_body else {}
    processing_time = data.get("processing_time", 0.1)
    await asyncio.sleep(processing_time)
    return web.json_response({
        "processed": True,
        "processing_time": processing_time,
        "timestamp": time.time()
    })

app_start_time = time.time()
app = web.Application()
app.router.add_get('/health', health_check)
app.router.add_get('/ready', ready_check)
app.router.add_post('/stress', stress_endpoint)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8000)
'''
        
        # Save application code to evidence directory
        app_file = self.evidence_dir / "test_application.py"
        with open(app_file, 'w') as f:
            f.write(app_code)
        
        # Create Dockerfile for test application
        dockerfile_content = '''
FROM python:3.9-slim
RUN pip install aiohttp
COPY test_application.py /app/test_application.py
WORKDIR /app
EXPOSE 8000
CMD ["python", "test_application.py"]
'''
        
        dockerfile = self.evidence_dir / "Dockerfile"
        with open(dockerfile, 'w') as f:
            f.write(dockerfile_content)
        
        # Build test application image
        image_tag = f"chaos_test_app:{int(time.time())}"
        self.docker_client.images.build(
            path=str(self.evidence_dir),
            tag=image_tag,
            rm=True
        )
        
        # Start multiple application instances
        for i in range(2):
            start_time = time.time()
            
            container = self.docker_client.containers.run(
                image_tag,
                name=f"chaos_app_{i}_{int(time.time())}",
                ports={'8000/tcp': None},
                detach=True,
                remove=False,
                network=self.networks['test_network'].name
            )
            
            # Get actual port mapping
            container.reload()
            app_port = container.ports['8000/tcp'][0]['HostPort']
            
            component = InfrastructureComponent(
                name=f"test_app_{i}",
                component_type="application",
                container=container,
                container_id=container.id,
                port=int(app_port),
                health_endpoint=f"http://localhost:{app_port}/health",
                startup_time=time.time() - start_time
            )
            
            applications.append(component)
            logger.info(f"Test application {i} started: {component.container_id[:12]} on port {component.port}")
        
        return applications
    
    async def _wait_for_infrastructure_ready(self) -> None:
        """Wait for all infrastructure components to be healthy"""
        
        logger.info("Waiting for infrastructure components to be ready...")
        
        for name, component in self.infrastructure_components.items():
            if component.health_endpoint:
                await self._wait_for_service_health(component, timeout=120)
            elif component.component_type == "kafka":
                await self._wait_for_kafka_ready(component, timeout=120)
            else:
                # Give other services time to start
                await asyncio.sleep(5)
        
        logger.info("All infrastructure components are ready")
    
    async def _wait_for_service_health(self, component: InfrastructureComponent, timeout: int = 60) -> None:
        """Wait for a service to become healthy"""
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(component.health_endpoint, timeout=5)
                if response.status_code == 200:
                    component.is_healthy = True
                    logger.info(f"Service {component.name} is healthy")
                    return
            except requests.exceptions.RequestException:
                pass  # Continue waiting
            
            await asyncio.sleep(2)
        
        raise RuntimeError(f"Service {component.name} failed to become healthy within {timeout} seconds")
    
    async def _wait_for_kafka_ready(self, component: InfrastructureComponent, timeout: int = 90) -> None:
        """Wait for Kafka to be ready using kafka-topics command"""
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Try to list topics to verify Kafka is ready
                result = component.container.exec_run(
                    "kafka-topics --bootstrap-server localhost:9092 --list",
                    timeout=10
                )
                
                if result.exit_code == 0:
                    component.is_healthy = True
                    logger.info(f"Kafka {component.name} is ready")
                    return
                    
            except Exception:
                pass  # Continue waiting
            
            await asyncio.sleep(3)
        
        raise RuntimeError(f"Kafka {component.name} failed to become ready within {timeout} seconds")
    
    async def execute_real_network_partition(self, scenario: ChaosScenario) -> ChaosTestResult:
        """Execute real network partition using Docker network isolation"""
        
        logger.info(f"Executing network partition scenario: {scenario.name}")
        
        start_time = datetime.now()
        infrastructure_before = await self._capture_infrastructure_state()
        
        # Create isolated network
        isolated_network = self.docker_client.networks.create(
            f"isolated_{int(time.time())}",
            driver="bridge"
        )
        
        partitioned_containers = []
        original_network = self.networks['test_network']
        
        try:
            # Move target components to isolated network
            for component_name in scenario.target_components:
                if component_name in self.infrastructure_components:
                    component = self.infrastructure_components[component_name]
                    
                    # Disconnect from original network
                    original_network.disconnect(component.container)
                    
                    # Connect to isolated network
                    isolated_network.connect(component.container)
                    
                    partitioned_containers.append(component)
                    logger.info(f"Partitioned component: {component.name}")
            
            # Monitor system behavior during partition
            behavior_metrics = await self._monitor_system_behavior_during_failure(
                scenario.duration_seconds
            )
            
            # Sleep for partition duration
            await asyncio.sleep(scenario.duration_seconds)
            
            failure_successful = len(partitioned_containers) > 0
            
        finally:
            # Heal the partition - reconnect to original network
            recovery_start = time.time()
            
            for component in partitioned_containers:
                try:
                    isolated_network.disconnect(component.container)
                    original_network.connect(component.container)
                    logger.info(f"Reconnected component: {component.name}")
                except Exception as e:
                    logger.error(f"Failed to reconnect {component.name}: {e}")
            
            # Clean up isolated network
            try:
                isolated_network.remove()
            except Exception as e:
                logger.error(f"Failed to remove isolated network: {e}")
            
            # Wait for system recovery
            recovery_successful, recovery_time = await self._wait_for_system_recovery(
                scenario.recovery_time_limit
            )
        
        end_time = datetime.now()
        infrastructure_after = await self._capture_infrastructure_state()
        
        # Generate evidence artifacts
        evidence_artifacts = await self._generate_scenario_evidence(
            scenario, behavior_metrics, infrastructure_before, infrastructure_after
        )
        
        return ChaosTestResult(
            scenario=scenario,
            start_time=start_time,
            end_time=end_time,
            infrastructure_state_before=infrastructure_before,
            infrastructure_state_after=infrastructure_after,
            failure_injection_successful=failure_successful,
            system_behavior_during_failure=behavior_metrics,
            recovery_successful=recovery_successful,
            recovery_time_seconds=recovery_time,
            measured_resilience_metrics=self._calculate_comprehensive_resilience_metrics(behavior_metrics),
            evidence_artifacts=evidence_artifacts,
            correlation_id=self.correlation_id,
            raw_monitoring_data=behavior_metrics.get("raw_data", []),
            container_logs_during_failure=await self._collect_container_logs_during_failure(),
            network_analysis_data=await self._collect_network_analysis_data()
        )
    
    async def execute_real_resource_exhaustion(self, scenario: ChaosScenario) -> ChaosTestResult:
        """Execute real resource exhaustion using Docker resource limits"""
        
        logger.info(f"Executing resource exhaustion scenario: {scenario.name}")
        
        start_time = datetime.now()
        infrastructure_before = await self._capture_infrastructure_state()
        
        constrained_containers = []
        original_configs = {}
        
        try:
            # Apply resource constraints to target components
            for component_name in scenario.target_components:
                if component_name in self.infrastructure_components:
                    component = self.infrastructure_components[component_name]
                    
                    # Store original configuration
                    original_configs[component_name] = {
                        'memory': component.container.attrs['HostConfig']['Memory'],
                        'cpu_quota': component.container.attrs['HostConfig']['CpuQuota']
                    }
                    
                    # Calculate constrained resources
                    if scenario.scenario_type == "memory_exhaustion":
                        # Limit memory to a small amount
                        new_memory = 128 * 1024 * 1024  # 128MB
                        component.container.update(mem_limit=new_memory)
                        
                    elif scenario.scenario_type == "cpu_exhaustion":
                        # Limit CPU to 10% of one core
                        component.container.update(cpu_quota=10000, cpu_period=100000)
                    
                    constrained_containers.append(component)
                    logger.info(f"Applied resource constraints to: {component.name}")
            
            # Monitor system behavior during resource exhaustion
            behavior_metrics = await self._monitor_system_behavior_during_failure(
                scenario.duration_seconds
            )
            
            # Apply additional stress if needed
            await self._apply_resource_stress(constrained_containers, scenario)
            
            # Sleep for scenario duration
            await asyncio.sleep(scenario.duration_seconds)
            
            failure_successful = len(constrained_containers) > 0
            
        finally:
            # Remove resource constraints
            recovery_start = time.time()
            
            for component in constrained_containers:
                try:
                    component_name = component.name
                    if component_name in original_configs:
                        config = original_configs[component_name]
                        component.container.update(
                            mem_limit=config['memory'] if config['memory'] > 0 else None,
                            cpu_quota=config['cpu_quota'] if config['cpu_quota'] > 0 else -1
                        )
                    logger.info(f"Removed constraints from: {component.name}")
                except Exception as e:
                    logger.error(f"Failed to remove constraints from {component.name}: {e}")
            
            # Wait for system recovery
            recovery_successful, recovery_time = await self._wait_for_system_recovery(
                scenario.recovery_time_limit
            )
        
        end_time = datetime.now()
        infrastructure_after = await self._capture_infrastructure_state()
        
        # Generate evidence artifacts
        evidence_artifacts = await self._generate_scenario_evidence(
            scenario, behavior_metrics, infrastructure_before, infrastructure_after
        )
        
        return ChaosTestResult(
            scenario=scenario,
            start_time=start_time,
            end_time=end_time,
            infrastructure_state_before=infrastructure_before,
            infrastructure_state_after=infrastructure_after,
            failure_injection_successful=failure_successful,
            system_behavior_during_failure=behavior_metrics,
            recovery_successful=recovery_successful,
            recovery_time_seconds=recovery_time,
            measured_resilience_metrics=self._calculate_comprehensive_resilience_metrics(behavior_metrics),
            evidence_artifacts=evidence_artifacts,
            correlation_id=self.correlation_id,
            raw_monitoring_data=behavior_metrics.get("raw_data", []),
            container_logs_during_failure=await self._collect_container_logs_during_failure(),
            network_analysis_data=await self._collect_network_analysis_data()
        )
    
    async def execute_real_service_failure(self, scenario: ChaosScenario) -> ChaosTestResult:
        """Execute real service failure by stopping containers"""
        
        logger.info(f"Executing service failure scenario: {scenario.name}")
        
        start_time = datetime.now()
        infrastructure_before = await self._capture_infrastructure_state()
        
        failed_containers = []
        
        try:
            # Stop target services
            for component_name in scenario.target_components:
                if component_name in self.infrastructure_components:
                    component = self.infrastructure_components[component_name]
                    
                    # Stop the container
                    component.container.stop()
                    component.is_healthy = False
                    
                    failed_containers.append(component)
                    logger.info(f"Stopped service: {component.name}")
            
            # Monitor system behavior during service failure
            behavior_metrics = await self._monitor_system_behavior_during_failure(
                scenario.duration_seconds
            )
            
            # Sleep for scenario duration
            await asyncio.sleep(scenario.duration_seconds)
            
            failure_successful = len(failed_containers) > 0
            
        finally:
            # Restart failed services
            recovery_start = time.time()
            
            for component in failed_containers:
                try:
                    component.container.start()
                    
                    # Wait for service to be healthy again
                    if component.health_endpoint:
                        await self._wait_for_service_health(component, timeout=60)
                    elif component.component_type == "kafka":
                        await self._wait_for_kafka_ready(component, timeout=60)
                    
                    logger.info(f"Restarted service: {component.name}")
                except Exception as e:
                    logger.error(f"Failed to restart {component.name}: {e}")
            
            # Wait for system recovery
            recovery_successful, recovery_time = await self._wait_for_system_recovery(
                scenario.recovery_time_limit
            )
        
        end_time = datetime.now()
        infrastructure_after = await self._capture_infrastructure_state()
        
        # Generate evidence artifacts
        evidence_artifacts = await self._generate_scenario_evidence(
            scenario, behavior_metrics, infrastructure_before, infrastructure_after
        )
        
        return ChaosTestResult(
            scenario=scenario,
            start_time=start_time,
            end_time=end_time,
            infrastructure_state_before=infrastructure_before,
            infrastructure_state_after=infrastructure_after,
            failure_injection_successful=failure_successful,
            system_behavior_during_failure=behavior_metrics,
            recovery_successful=recovery_successful,
            recovery_time_seconds=recovery_time,
            measured_resilience_metrics=self._calculate_comprehensive_resilience_metrics(behavior_metrics),
            evidence_artifacts=evidence_artifacts,
            correlation_id=self.correlation_id,
            raw_monitoring_data=behavior_metrics.get("raw_data", []),
            container_logs_during_failure=await self._collect_container_logs_during_failure(),
            network_analysis_data=await self._collect_network_analysis_data()
        )
    
    async def _monitor_system_behavior_during_failure(self, duration_seconds: int) -> Dict[str, Any]:
        """Monitor system behavior during failure injection"""
        
        metrics = {
            "start_time": time.time(),
            "duration_seconds": duration_seconds,
            "http_responses": [],
            "error_rates": [],
            "response_times": [],
            "container_stats": [],
            "network_connectivity": []
        }
        
        monitoring_interval = 5  # seconds
        monitoring_count = duration_seconds // monitoring_interval
        
        for i in range(monitoring_count):
            iteration_start = time.time()
            
            # Test HTTP endpoints
            http_results = await self._test_http_endpoints()
            metrics["http_responses"].append({
                "timestamp": iteration_start,
                "results": http_results
            })
            
            # Collect container statistics
            container_stats = await self._collect_container_statistics()
            metrics["container_stats"].append({
                "timestamp": iteration_start,
                "stats": container_stats
            })
            
            # Test network connectivity
            connectivity_results = await self._test_network_connectivity()
            metrics["network_connectivity"].append({
                "timestamp": iteration_start,
                "results": connectivity_results
            })
            
            # Calculate error rates and response times
            if http_results:
                successful_requests = sum(1 for r in http_results if r.get("success", False))
                total_requests = len(http_results)
                error_rate = (total_requests - successful_requests) / total_requests if total_requests > 0 else 1.0
                
                response_times = [r.get("response_time", 0) for r in http_results if r.get("response_time")]
                avg_response_time = sum(response_times) / len(response_times) if response_times else 0
                
                metrics["error_rates"].append({
                    "timestamp": iteration_start,
                    "error_rate": error_rate,
                    "total_requests": total_requests,
                    "successful_requests": successful_requests
                })
                
                metrics["response_times"].append({
                    "timestamp": iteration_start,
                    "avg_response_time": avg_response_time,
                    "response_times": response_times
                })
            
            # Wait for next monitoring interval
            await asyncio.sleep(monitoring_interval)
        
        metrics["end_time"] = time.time()
        return metrics
    
    async def _test_http_endpoints(self) -> List[Dict[str, Any]]:
        """Test HTTP endpoints of running services"""
        
        results = []
        
        for name, component in self.infrastructure_components.items():
            if component.component_type == "application" and component.health_endpoint:
                try:
                    start_time = time.time()
                    response = requests.get(component.health_endpoint, timeout=5)
                    response_time = time.time() - start_time
                    
                    results.append({
                        "component": name,
                        "endpoint": component.health_endpoint,
                        "status_code": response.status_code,
                        "response_time": response_time,
                        "success": response.status_code == 200,
                        "error": None
                    })
                    
                except Exception as e:
                    results.append({
                        "component": name,
                        "endpoint": component.health_endpoint,
                        "status_code": None,
                        "response_time": None,
                        "success": False,
                        "error": str(e)
                    })
        
        return results
    
    async def _collect_container_statistics(self) -> Dict[str, Any]:
        """Collect statistics from all containers"""
        
        stats = {}
        
        for name, component in self.infrastructure_components.items():
            try:
                container = component.container
                container.reload()
                
                # Get container stats
                stats_stream = container.stats(stream=False)
                
                # Calculate CPU and memory usage
                cpu_stats = stats_stream['cpu_stats']
                precpu_stats = stats_stream['precpu_stats']
                memory_stats = stats_stream['memory_stats']
                
                # CPU usage calculation
                cpu_delta = cpu_stats['cpu_usage']['total_usage'] - precpu_stats['cpu_usage']['total_usage']
                system_delta = cpu_stats['system_cpu_usage'] - precpu_stats['system_cpu_usage']
                cpu_usage = (cpu_delta / system_delta) * len(cpu_stats['cpu_usage']['percpu_usage']) * 100.0
                
                # Memory usage
                memory_usage = memory_stats['usage']
                memory_limit = memory_stats['limit']
                memory_percent = (memory_usage / memory_limit) * 100.0
                
                stats[name] = {
                    "container_id": container.id[:12],
                    "status": container.status,
                    "cpu_usage_percent": cpu_usage,
                    "memory_usage_bytes": memory_usage,
                    "memory_usage_percent": memory_percent,
                    "memory_limit_bytes": memory_limit
                }
                
            except Exception as e:
                stats[name] = {
                    "error": str(e),
                    "status": "unknown"
                }
        
        return stats
    
    async def _test_network_connectivity(self) -> Dict[str, Any]:
        """Test network connectivity between components"""
        
        connectivity = {}
        
        # Test connectivity between application instances
        app_components = [comp for comp in self.infrastructure_components.values() 
                         if comp.component_type == "application"]
        
        for i, source_comp in enumerate(app_components):
            for j, target_comp in enumerate(app_components):
                if i != j:
                    test_name = f"{source_comp.name}_to_{target_comp.name}"
                    
                    try:
                        # Use ping to test connectivity
                        result = source_comp.container.exec_run(
                            f"ping -c 1 -W 1 {target_comp.container.name}",
                            timeout=5
                        )
                        
                        connectivity[test_name] = {
                            "success": result.exit_code == 0,
                            "output": result.output.decode() if result.output else "",
                            "exit_code": result.exit_code
                        }
                        
                    except Exception as e:
                        connectivity[test_name] = {
                            "success": False,
                            "error": str(e)
                        }
        
        return connectivity
    
    async def _apply_resource_stress(self, components: List[InfrastructureComponent], 
                                   scenario: ChaosScenario) -> None:
        """Apply additional resource stress to components"""
        
        for component in components:
            if component.component_type == "application":
                try:
                    # Apply CPU stress
                    if "cpu" in scenario.scenario_type:
                        component.container.exec_run(
                            "sh -c 'yes > /dev/null &'",
                            detach=True
                        )
                    
                    # Apply memory stress
                    if "memory" in scenario.scenario_type:
                        component.container.exec_run(
                            "sh -c 'dd if=/dev/zero of=/tmp/stress bs=1M count=100 &'",
                            detach=True
                        )
                        
                except Exception as e:
                    logger.warning(f"Failed to apply stress to {component.name}: {e}")
    
    async def _wait_for_system_recovery(self, timeout_seconds: int) -> tuple[bool, float]:
        """Wait for system to recover from failure"""
        
        recovery_start = time.time()
        
        while time.time() - recovery_start < timeout_seconds:
            # Test if all healthy components are responding
            all_healthy = True
            
            for name, component in self.infrastructure_components.items():
                if component.health_endpoint:
                    try:
                        response = requests.get(component.health_endpoint, timeout=3)
                        if response.status_code != 200:
                            all_healthy = False
                            break
                    except Exception:
                        all_healthy = False
                        break
            
            if all_healthy:
                recovery_time = time.time() - recovery_start
                logger.info(f"System recovered in {recovery_time:.2f} seconds")
                return True, recovery_time
            
            await asyncio.sleep(2)
        
        recovery_time = time.time() - recovery_start
        logger.warning(f"System failed to recover within {timeout_seconds} seconds")
        return False, recovery_time
    
    async def _capture_infrastructure_state(self) -> Dict[str, Any]:
        """Capture current state of infrastructure"""
        
        state = {
            "timestamp": time.time(),
            "components": {},
            "networks": {},
            "system_metrics": {}
        }
        
        # Capture component states
        for name, component in self.infrastructure_components.items():
            try:
                component.container.reload()
                state["components"][name] = {
                    "container_id": component.container.id,
                    "status": component.container.status,
                    "health_endpoint": component.health_endpoint,
                    "is_healthy": component.is_healthy,
                    "ports": component.container.ports,
                    "image": component.container.image.tags[0] if component.container.image.tags else "unknown"
                }
            except Exception as e:
                state["components"][name] = {"error": str(e)}
        
        # Capture network states
        for name, network in self.networks.items():
            try:
                network.reload()
                state["networks"][name] = {
                    "id": network.id,
                    "name": network.name,
                    "driver": network.attrs.get("Driver", "unknown"),
                    "scope": network.attrs.get("Scope", "unknown"),
                    "containers": len(network.attrs.get("Containers", {}))
                }
            except Exception as e:
                state["networks"][name] = {"error": str(e)}
        
        # Capture system metrics
        try:
            state["system_metrics"] = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            }
        except Exception as e:
            state["system_metrics"] = {"error": str(e)}
        
        return state
    
    def _calculate_statistical_metrics(self, data_points: List[float]) -> StatisticalMetrics:
        """Calculate comprehensive statistical metrics with confidence intervals"""
        
        if not data_points or len(data_points) == 0:
            return StatisticalMetrics(
                mean=0.0, median=0.0, std_dev=0.0, min_value=0.0, max_value=0.0,
                percentile_95=0.0, percentile_99=0.0, sample_size=0,
                confidence_interval_95=(0.0, 0.0)
            )
        
        # Sort data for percentile calculations
        sorted_data = sorted(data_points)
        n = len(sorted_data)
        
        # Basic statistics
        mean_val = statistics.mean(data_points)
        median_val = statistics.median(data_points)
        std_dev = statistics.stdev(data_points) if n > 1 else 0.0
        min_val = min(data_points)
        max_val = max(data_points)
        
        # Percentiles
        percentile_95 = np.percentile(sorted_data, 95) if n > 0 else 0.0
        percentile_99 = np.percentile(sorted_data, 99) if n > 0 else 0.0
        
        # 95% confidence interval for mean
        if n > 1:
            # t-distribution critical value for 95% confidence (approximation)
            t_critical = 1.96 if n >= 30 else 2.576  # Conservative estimate for small samples
            margin_error = t_critical * (std_dev / np.sqrt(n))
            confidence_interval = (mean_val - margin_error, mean_val + margin_error)
        else:
            confidence_interval = (mean_val, mean_val)
        
        return StatisticalMetrics(
            mean=mean_val,
            median=median_val,
            std_dev=std_dev,
            min_value=min_val,
            max_value=max_val,
            percentile_95=percentile_95,
            percentile_99=percentile_99,
            sample_size=n,
            confidence_interval_95=confidence_interval
        )
    
    def _calculate_comprehensive_resilience_metrics(self, behavior_metrics: Dict[str, Any]) -> ComprehensiveResilienceMetrics:
        """Calculate comprehensive resilience metrics with full statistical analysis"""
        
        logger.info("Calculating comprehensive resilience metrics with statistical analysis")
        
        measurement_start = behavior_metrics.get("start_time", time.time())
        measurement_end = behavior_metrics.get("end_time", time.time())
        measurement_period = measurement_end - measurement_start
        
        # Extract raw data for statistical analysis
        availability_data = []
        error_rate_data = []
        response_time_data = []
        recovery_time_data = []
        
        # Process HTTP response data
        if behavior_metrics.get("http_responses"):
            for response_batch in behavior_metrics["http_responses"]:
                successful_requests = 0
                total_requests = 0
                batch_response_times = []
                
                for result in response_batch["results"]:
                    total_requests += 1
                    if result.get("success", False):
                        successful_requests += 1
                    
                    if result.get("response_time"):
                        batch_response_times.append(result["response_time"])
                        response_time_data.append(result["response_time"])
                
                if total_requests > 0:
                    availability = successful_requests / total_requests
                    availability_data.append(availability)
                    error_rate_data.append(1.0 - availability)
        
        # Process recovery time data
        if behavior_metrics.get("recovery_events"):
            for recovery_event in behavior_metrics["recovery_events"]:
                if recovery_event.get("recovery_time"):
                    recovery_time_data.append(recovery_event["recovery_time"])
        
        # Calculate statistical metrics for each dimension
        availability_stats = self._calculate_statistical_metrics(availability_data)
        error_rate_stats = self._calculate_statistical_metrics(error_rate_data)
        response_time_stats = self._calculate_statistical_metrics(response_time_data)
        recovery_time_stats = self._calculate_statistical_metrics(recovery_time_data)
        
        # Calculate normalized scores (0.0 to 1.0)
        availability_score = availability_stats.mean
        error_tolerance_score = max(0.0, 1.0 - error_rate_stats.mean)
        
        # Performance score based on response time (threshold: 5 seconds)
        if response_time_stats.mean > 0:
            performance_score = max(0.0, min(1.0, (5.0 - response_time_stats.mean) / 5.0))
        else:
            performance_score = 1.0
        
        # Recovery score based on recovery time (threshold: 60 seconds)
        if recovery_time_stats.mean > 0:
            recovery_score = max(0.0, min(1.0, (60.0 - recovery_time_stats.mean) / 60.0))
        else:
            recovery_score = 1.0
        
        # Overall resilience score (weighted combination)
        overall_score = (
            availability_score * 0.35 +
            error_tolerance_score * 0.25 +
            performance_score * 0.25 +
            recovery_score * 0.15
        )
        
        # Statistical confidence based on sample size and variance
        total_samples = (availability_stats.sample_size + 
                        error_rate_stats.sample_size + 
                        response_time_stats.sample_size)
        
        if total_samples >= self.sample_size_minimum * 3:
            statistical_confidence = 0.95
        elif total_samples >= self.sample_size_minimum:
            statistical_confidence = 0.80
        else:
            statistical_confidence = 0.60
        
        logger.info(f"Resilience metrics calculated: "
                   f"availability={availability_score:.3f}, "
                   f"error_tolerance={error_tolerance_score:.3f}, "
                   f"performance={performance_score:.3f}, "
                   f"recovery={recovery_score:.3f}, "
                   f"overall={overall_score:.3f}, "
                   f"confidence={statistical_confidence:.2f}")
        
        return ComprehensiveResilienceMetrics(
            availability_score=availability_score,
            availability_stats=availability_stats,
            recovery_time_score=recovery_score,
            recovery_time_stats=recovery_time_stats,
            error_tolerance_score=error_tolerance_score,
            error_rate_stats=error_rate_stats,
            performance_degradation_score=performance_score,
            response_time_stats=response_time_stats,
            overall_resilience_score=overall_score,
            statistical_confidence=statistical_confidence,
            measurement_period_seconds=measurement_period,
            sample_count=total_samples
        )
    
    async def _collect_container_logs_during_failure(self) -> Dict[str, str]:
        """Collect real container logs during failure injection for evidence"""
        
        logger.info("Collecting container logs during failure for evidence")
        
        container_logs = {}
        
        for name, component in self.infrastructure_components.items():
            try:
                # Get recent logs (last 500 lines) with timestamps
                logs = component.container.logs(timestamps=True, tail=500).decode('utf-8')
                container_logs[name] = logs
                
                logger.debug(f"Collected {len(logs.splitlines())} log lines from {name}")
                
            except Exception as e:
                logger.warning(f"Failed to collect logs from {name}: {e}")
                container_logs[name] = f"ERROR: Failed to collect logs - {e}"
        
        return container_logs
    
    async def _collect_network_analysis_data(self) -> Dict[str, Any]:
        """Collect comprehensive network analysis data during failure"""
        
        logger.info("Collecting network analysis data")
        
        network_data = {
            "timestamp": datetime.now().isoformat(),
            "network_topology": {},
            "connectivity_matrix": {},
            "traffic_analysis": {},
            "failure_impact_analysis": {}
        }
        
        # Analyze network topology
        for name, network in self.networks.items():
            try:
                network.reload()
                network_data["network_topology"][name] = {
                    "id": network.id,
                    "name": network.name,
                    "driver": network.attrs.get("Driver", "unknown"),
                    "scope": network.attrs.get("Scope", "unknown"),
                    "containers": list(network.attrs.get("Containers", {}).keys()),
                    "subnet": network.attrs.get("IPAM", {}).get("Config", [{}])[0].get("Subnet", "unknown")
                }
            except Exception as e:
                logger.warning(f"Failed to analyze network {name}: {e}")
                network_data["network_topology"][name] = {"error": str(e)}
        
        # Build connectivity matrix
        connectivity_results = await self._test_network_connectivity()
        network_data["connectivity_matrix"] = connectivity_results
        
        # Analyze traffic patterns (simplified)
        traffic_analysis = await self._analyze_network_traffic()
        network_data["traffic_analysis"] = traffic_analysis
        
        # Failure impact analysis
        failure_impact = await self._analyze_failure_network_impact()
        network_data["failure_impact_analysis"] = failure_impact
        
        return network_data
    
    async def _analyze_network_traffic(self) -> Dict[str, Any]:
        """Analyze network traffic patterns during chaos scenarios"""
        
        traffic_data = {
            "total_connections": 0,
            "successful_connections": 0,
            "failed_connections": 0,
            "average_latency_ms": 0.0,
            "packet_loss_percentage": 0.0
        }
        
        # Simplified traffic analysis using container network stats
        for name, component in self.infrastructure_components.items():
            try:
                stats = component.container.stats(stream=False)
                networks = stats.get("networks", {})
                
                for net_name, net_stats in networks.items():
                    traffic_data["total_connections"] += net_stats.get("rx_packets", 0)
                    
            except Exception as e:
                logger.debug(f"Failed to collect network stats from {name}: {e}")
        
        return traffic_data
    
    async def _analyze_failure_network_impact(self) -> Dict[str, Any]:
        """Analyze how failures impact network connectivity and performance"""
        
        impact_analysis = {
            "isolated_components": [],
            "degraded_paths": [],
            "alternative_routes": [],
            "recovery_paths": []
        }
        
        # Test connectivity between all components
        app_components = [comp for comp in self.infrastructure_components.values() 
                         if comp.component_type == "application"]
        
        for source in app_components:
            for target in app_components:
                if source != target:
                    try:
                        # Test if components can reach each other
                        result = source.container.exec_run(
                            f"ping -c 1 -W 2 {target.container.name}",
                            timeout=5
                        )
                        
                        if result.exit_code != 0:
                            impact_analysis["isolated_components"].append({
                                "source": source.name,
                                "target": target.name,
                                "isolation_type": "network_partition"
                            })
                        
                    except Exception as e:
                        logger.debug(f"Network impact test failed {source.name} -> {target.name}: {e}")
        
        return impact_analysis
    
    async def _generate_scenario_evidence(self, scenario: ChaosScenario, 
                                        behavior_metrics: Dict[str, Any],
                                        infrastructure_before: Dict[str, Any],
                                        infrastructure_after: Dict[str, Any]) -> List[str]:
        """Generate evidence artifacts for a chaos scenario"""
        
        evidence_files = []
        
        # Generate scenario report
        scenario_report = {
            "scenario": asdict(scenario),
            "behavior_metrics": behavior_metrics,
            "infrastructure_before": infrastructure_before,
            "infrastructure_after": infrastructure_after,
            "generated_at": datetime.now().isoformat()
        }
        
        scenario_file = self.evidence_dir / f"scenario_{scenario.name}_{int(time.time())}.json"
        with open(scenario_file, 'w') as f:
            json.dump(scenario_report, f, indent=2, default=str)
        evidence_files.append(str(scenario_file))
        
        # Generate container logs
        for name, component in self.infrastructure_components.items():
            try:
                logs = component.container.logs(timestamps=True, tail=1000).decode()
                log_file = self.evidence_dir / f"container_logs_{name}_{scenario.name}.txt"
                with open(log_file, 'w') as f:
                    f.write(logs)
                evidence_files.append(str(log_file))
            except Exception as e:
                logger.warning(f"Failed to collect logs for {name}: {e}")
        
        # Generate network analysis
        network_analysis = {
            "networks": {name: net.attrs for name, net in self.networks.items()},
            "scenario": scenario.name,
            "timestamp": datetime.now().isoformat()
        }
        
        network_file = self.evidence_dir / f"network_analysis_{scenario.name}.json"
        with open(network_file, 'w') as f:
            json.dump(network_analysis, f, indent=2, default=str)
        evidence_files.append(str(network_file))
        
        return evidence_files
    
    async def _generate_infrastructure_evidence(self, phase: str) -> None:
        """Generate evidence documentation for infrastructure state"""
        
        evidence = {
            "phase": phase,
            "timestamp": datetime.now().isoformat(),
            "infrastructure_components": {},
            "docker_info": {},
            "system_info": {}
        }
        
        # Document infrastructure components
        for name, component in self.infrastructure_components.items():
            evidence["infrastructure_components"][name] = {
                "name": component.name,
                "type": component.component_type,
                "container_id": component.container_id,
                "port": component.port,
                "health_endpoint": component.health_endpoint,
                "startup_time": component.startup_time,
                "is_healthy": component.is_healthy
            }
        
        # Document Docker environment
        try:
            docker_info = self.docker_client.info()
            evidence["docker_info"] = {
                "version": docker_info.get("ServerVersion"),
                "containers_running": docker_info.get("ContainersRunning"),
                "images": docker_info.get("Images"),
                "driver": docker_info.get("Driver")
            }
        except Exception as e:
            evidence["docker_info"] = {"error": str(e)}
        
        # Document system information
        try:
            evidence["system_info"] = {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "platform": platform.platform()
            }
        except Exception as e:
            evidence["system_info"] = {"error": str(e)}
        
        evidence_file = self.evidence_dir / f"infrastructure_{phase}_{int(time.time())}.json"
        with open(evidence_file, 'w') as f:
            json.dump(evidence, f, indent=2, default=str)
    
    async def cleanup_infrastructure(self) -> None:
        """Clean up all test infrastructure"""
        
        logger.info("Cleaning up chaos engineering test infrastructure")
        
        # Stop and remove containers
        for name, component in self.infrastructure_components.items():
            try:
                component.container.stop(timeout=10)
                component.container.remove()
                logger.info(f"Cleaned up container: {name}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {name}: {e}")
        
        # Remove networks
        for name, network in self.networks.items():
            try:
                network.remove()
                logger.info(f"Cleaned up network: {name}")
            except Exception as e:
                logger.warning(f"Failed to cleanup network {name}: {e}")
        
        # Generate final evidence
        await self._generate_infrastructure_evidence("cleanup_complete")
        
        logger.info(f"Evidence collected in: {self.evidence_dir}")
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive chaos engineering test report"""
        
        total_scenarios = len(self.test_results)
        successful_scenarios = len([r for r in self.test_results if r.recovery_successful])
        
        # Calculate aggregate resilience metrics
        aggregate_metrics = {
            "availability_score": 0.0,
            "recovery_score": 0.0,
            "error_tolerance_score": 0.0,
            "performance_degradation_score": 0.0
        }
        
        if self.test_results:
            for metric in aggregate_metrics.keys():
                values = [getattr(r.measured_resilience_metrics, metric, 0.0) for r in self.test_results]
                aggregate_metrics[metric] = sum(values) / len(values)
        
        return {
            "test_name": self.test_name,
            "summary": {
                "total_scenarios": total_scenarios,
                "successful_scenarios": successful_scenarios,
                "success_rate": (successful_scenarios / total_scenarios * 100) if total_scenarios > 0 else 0,
                "aggregate_resilience_metrics": aggregate_metrics
            },
            "scenarios": [asdict(result) for result in self.test_results],
            "evidence_directory": str(self.evidence_dir),
            "infrastructure_components": len(self.infrastructure_components),
            "test_duration": (
                max([r.end_time for r in self.test_results]) - 
                min([r.start_time for r in self.test_results])
            ).total_seconds() if self.test_results else 0
        } 