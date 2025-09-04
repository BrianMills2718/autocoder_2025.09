#!/usr/bin/env python3
"""
Resource Prediction - P0.8-E2 Intelligent Resource Allocation

Implements intelligent port and resource allocation for component systems.
"""
import asyncio
import socket
import psutil
import threading
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import random
import time
from pathlib import Path
import json

from autocoder_cc.observability import get_logger, get_metrics_collector, get_tracer
from autocoder_cc.blueprint_language.system_blueprint_parser import ParsedSystemBlueprint, ParsedComponent

logger = get_logger(__name__)


class ResourceType(Enum):
    """Types of resources that can be allocated"""
    PORT = "port"
    MEMORY = "memory"
    CPU = "cpu"
    DISK = "disk"
    NETWORK_BANDWIDTH = "network_bandwidth"
    DATABASE_CONNECTION = "database_connection"
    CACHE_SIZE = "cache_size"


class PortType(Enum):
    """Types of ports for different services"""
    HTTP = "http"
    HTTPS = "https"
    DATABASE = "database"
    CACHE = "cache"
    MESSAGE_QUEUE = "message_queue"
    ADMIN = "admin"
    METRICS = "metrics"
    HEALTH_CHECK = "health_check"
    CUSTOM = "custom"


@dataclass
class ResourceRequirement:
    """Specification for a resource requirement"""
    resource_type: ResourceType
    min_value: Union[int, float]
    max_value: Union[int, float]
    preferred_value: Optional[Union[int, float]] = None
    priority: int = 1  # 1=low, 5=critical
    component_name: str = ""
    description: str = ""


@dataclass
class PortRequirement:
    """Specification for a port requirement"""
    port_type: PortType
    component_name: str
    service_name: str = ""
    preferred_port: Optional[int] = None
    port_range: Optional[Tuple[int, int]] = None
    external_access: bool = False
    ssl_required: bool = False
    description: str = ""


@dataclass
class AllocatedResource:
    """Represents an allocated resource"""
    resource_type: ResourceType
    allocated_value: Union[int, float]
    component_name: str
    allocation_time: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AllocatedPort:
    """Represents an allocated port"""
    port: int
    port_type: PortType
    component_name: str
    service_name: str
    external_access: bool
    ssl_required: bool
    allocation_time: float = field(default_factory=time.time)
    in_use: bool = False


@dataclass
class SystemResourceProfile:
    """Resource profile for an entire system"""
    system_name: str
    total_components: int
    estimated_memory_mb: int
    estimated_cpu_percent: float
    estimated_disk_mb: int
    estimated_network_mbps: float
    allocated_ports: List[AllocatedPort] = field(default_factory=list)
    allocated_resources: List[AllocatedResource] = field(default_factory=list)
    resource_conflicts: List[str] = field(default_factory=list)
    optimization_recommendations: List[str] = field(default_factory=list)


class PortAllocator:
    """Intelligent port allocation system"""
    
    def __init__(self):
        self.allocated_ports: Set[int] = set()
        self.port_assignments: Dict[str, AllocatedPort] = {}
        self.port_ranges: Dict[PortType, Tuple[int, int]] = {
            PortType.HTTP: (8000, 8099),
            PortType.HTTPS: (8443, 8499),
            PortType.DATABASE: (5432, 5499),
            PortType.CACHE: (6379, 6399),
            PortType.MESSAGE_QUEUE: (5672, 5699),
            PortType.ADMIN: (9000, 9099),
            PortType.METRICS: (9090, 9199),
            PortType.HEALTH_CHECK: (8080, 8089),
            PortType.CUSTOM: (10000, 19999)
        }
        self.metrics_collector = get_metrics_collector("port_allocator")
        self._lock = threading.RLock()
    
    def is_port_available(self, port: int) -> bool:
        """Check if a port is available on the system"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('localhost', port))
                return True
        except OSError:
            return False
    
    def find_available_port(self, port_type: PortType, preferred_port: Optional[int] = None) -> Optional[int]:
        """Find an available port of the specified type"""
        with self._lock:
            # Try preferred port first
            if preferred_port and self._is_port_suitable(preferred_port, port_type):
                if preferred_port not in self.allocated_ports and self.is_port_available(preferred_port):
                    return preferred_port
            
            # Try ports in the type-specific range
            start_port, end_port = self.port_ranges[port_type]
            
            # Try random ports first to avoid conflicts in concurrent allocations
            attempted_ports = set()
            for _ in range(min(50, end_port - start_port)):
                port = random.randint(start_port, end_port)
                if port in attempted_ports:
                    continue
                attempted_ports.add(port)
                
                if port not in self.allocated_ports and self.is_port_available(port):
                    return port
            
            # If random search failed, try sequential search
            for port in range(start_port, end_port + 1):
                if port not in attempted_ports and port not in self.allocated_ports and self.is_port_available(port):
                    return port
            
            return None
    
    def _is_port_suitable(self, port: int, port_type: PortType) -> bool:
        """Check if a port is suitable for the given type"""
        start_port, end_port = self.port_ranges[port_type]
        return start_port <= port <= end_port
    
    def allocate_port(self, requirement: PortRequirement) -> Optional[AllocatedPort]:
        """Allocate a port based on requirements"""
        with self._lock:
            port = self.find_available_port(requirement.port_type, requirement.preferred_port)
            
            if port is None:
                logger.error(f"Failed to allocate port for {requirement.component_name} ({requirement.port_type.value})")
                self.metrics_collector.record_error("port_allocation_failed")
                return None
            
            allocated_port = AllocatedPort(
                port=port,
                port_type=requirement.port_type,
                component_name=requirement.component_name,
                service_name=requirement.service_name,
                external_access=requirement.external_access,
                ssl_required=requirement.ssl_required
            )
            
            self.allocated_ports.add(port)
            assignment_key = f"{requirement.component_name}:{requirement.service_name}"
            self.port_assignments[assignment_key] = allocated_port
            
            logger.info(f"Allocated port {port} for {requirement.component_name}:{requirement.service_name}")
            self.metrics_collector.record_business_event("port_allocated", 1)
            
            return allocated_port
    
    def deallocate_port(self, component_name: str, service_name: str = "") -> bool:
        """Deallocate a port"""
        with self._lock:
            assignment_key = f"{component_name}:{service_name}"
            
            if assignment_key in self.port_assignments:
                allocated_port = self.port_assignments[assignment_key]
                self.allocated_ports.discard(allocated_port.port)
                del self.port_assignments[assignment_key]
                
                logger.info(f"Deallocated port {allocated_port.port} from {component_name}:{service_name}")
                self.metrics_collector.record_business_event("port_deallocated", 1)
                return True
            
            return False
    
    def get_port_allocation_summary(self) -> Dict[str, Any]:
        """Get summary of port allocations"""
        with self._lock:
            allocations_by_type = {}
            for allocated_port in self.port_assignments.values():
                port_type = allocated_port.port_type.value
                if port_type not in allocations_by_type:
                    allocations_by_type[port_type] = []
                allocations_by_type[port_type].append({
                    "port": allocated_port.port,
                    "component": allocated_port.component_name,
                    "service": allocated_port.service_name,
                    "external_access": allocated_port.external_access
                })
            
            return {
                "total_allocated_ports": len(self.allocated_ports),
                "allocations_by_type": allocations_by_type,
                "available_ranges": {
                    port_type.value: f"{start}-{end}" 
                    for port_type, (start, end) in self.port_ranges.items()
                }
            }


class ResourceEstimator:
    """Estimates resource requirements for components and systems"""
    
    def __init__(self):
        self.component_profiles: Dict[str, Dict[str, float]] = {
            "Source": {
                "memory_mb": 50,
                "cpu_percent": 5,
                "disk_mb": 10,
                "network_mbps": 1
            },
            "Transformer": {
                "memory_mb": 100,
                "cpu_percent": 15,
                "disk_mb": 20,
                "network_mbps": 2
            },
            "Sink": {
                "memory_mb": 75,
                "cpu_percent": 8,
                "disk_mb": 50,
                "network_mbps": 1
            },
            "Store": {
                "memory_mb": 200,
                "cpu_percent": 10,
                "disk_mb": 500,
                "network_mbps": 3
            },
            "APIEndpoint": {
                "memory_mb": 150,
                "cpu_percent": 20,
                "disk_mb": 30,
                "network_mbps": 10
            },
            "Model": {
                "memory_mb": 500,
                "cpu_percent": 50,
                "disk_mb": 100,
                "network_mbps": 5
            },
            "Router": {
                "memory_mb": 80,
                "cpu_percent": 12,
                "disk_mb": 15,
                "network_mbps": 15
            },
            "Aggregator": {
                "memory_mb": 120,
                "cpu_percent": 18,
                "disk_mb": 25,
                "network_mbps": 8
            }
        }
        self.system_overhead_factor = 1.2  # 20% overhead for system processes
        self.peak_load_factor = 1.5  # 50% buffer for peak loads
    
    def estimate_component_resources(self, component: ParsedComponent) -> Dict[str, float]:
        """Estimate resources for a single component"""
        component_type = component.type
        base_profile = self.component_profiles.get(component_type, self.component_profiles["Transformer"])
        
        # Apply scaling factors based on component configuration
        scaling_factor = self._calculate_scaling_factor(component)
        
        estimated_resources = {}
        for resource, base_value in base_profile.items():
            estimated_resources[resource] = base_value * scaling_factor
        
        return estimated_resources
    
    def _calculate_scaling_factor(self, component: ParsedComponent) -> float:
        """Calculate scaling factor based on component configuration"""
        scaling_factor = 1.0
        
        # Check configuration for scaling hints
        if hasattr(component, 'config') and component.config:
            config = component.config
            
            # Scale based on data volume hints
            if 'batch_size' in config:
                batch_size = config.get('batch_size', 10)
                scaling_factor *= max(1.0, batch_size / 10.0)
            
            if 'max_connections' in config:
                max_connections = config.get('max_connections', 10)
                scaling_factor *= max(1.0, max_connections / 10.0)
            
            if 'cache_size' in config:
                cache_size = config.get('cache_size', 100)
                scaling_factor *= max(1.0, cache_size / 100.0)
        
        # Apply component-specific scaling
        if component.type == "APIEndpoint":
            # API endpoints typically need more resources for concurrent connections
            scaling_factor *= 1.5
        elif component.type == "Model":
            # ML models need significantly more resources
            scaling_factor *= 2.0
        elif component.type == "Store":
            # Storage components need more memory and disk
            scaling_factor *= 1.3
        
        return min(scaling_factor, 5.0)  # Cap at 5x scaling
    
    def estimate_system_resources(self, system_blueprint: ParsedSystemBlueprint) -> SystemResourceProfile:
        """Estimate total system resource requirements"""
        total_memory = 0
        total_cpu = 0
        total_disk = 0
        total_network = 0
        
        component_estimates = {}
        
        # Estimate resources for each component
        for component in system_blueprint.system.components:
            component_resources = self.estimate_component_resources(component)
            component_estimates[component.name] = component_resources
            
            total_memory += component_resources.get('memory_mb', 0)
            total_cpu += component_resources.get('cpu_percent', 0)
            total_disk += component_resources.get('disk_mb', 0)
            total_network += component_resources.get('network_mbps', 0)
        
        # Apply system overhead and peak load factors
        total_memory *= self.system_overhead_factor * self.peak_load_factor
        total_cpu *= self.system_overhead_factor
        total_disk *= self.system_overhead_factor
        total_network *= self.peak_load_factor
        
        # Generate optimization recommendations
        recommendations = self._generate_optimization_recommendations(
            total_memory, total_cpu, total_disk, total_network, component_estimates
        )
        
        return SystemResourceProfile(
            system_name=system_blueprint.system.name,
            total_components=len(system_blueprint.system.components),
            estimated_memory_mb=int(total_memory),
            estimated_cpu_percent=min(total_cpu, 100),  # Cap at 100%
            estimated_disk_mb=int(total_disk),
            estimated_network_mbps=total_network,
            optimization_recommendations=recommendations
        )
    
    def _generate_optimization_recommendations(self, 
                                            memory_mb: float, 
                                            cpu_percent: float, 
                                            disk_mb: float, 
                                            network_mbps: float,
                                            component_estimates: Dict[str, Dict[str, float]]) -> List[str]:
        """Generate optimization recommendations based on resource estimates"""
        recommendations = []
        
        # Memory recommendations
        if memory_mb > 4096:  # > 4GB
            recommendations.append("Consider using memory-efficient data structures or external caching")
            recommendations.append("Implement memory pooling for large objects")
        
        if memory_mb > 8192:  # > 8GB
            recommendations.append("Consider horizontal scaling or component distribution")
        
        # CPU recommendations
        if cpu_percent > 80:
            recommendations.append("High CPU usage predicted - consider async processing patterns")
            recommendations.append("Implement CPU-bound task queuing or worker pools")
        
        # Disk recommendations
        if disk_mb > 10240:  # > 10GB
            recommendations.append("Consider external storage solutions or data compression")
            recommendations.append("Implement data archival and cleanup strategies")
        
        # Network recommendations
        if network_mbps > 50:
            recommendations.append("High network usage - consider data compression and caching")
            recommendations.append("Implement connection pooling and keep-alive strategies")
        
        # Component-specific recommendations
        high_memory_components = [
            name for name, resources in component_estimates.items() 
            if resources.get('memory_mb', 0) > 300
        ]
        
        if high_memory_components:
            recommendations.append(
                f"High memory components detected: {', '.join(high_memory_components)} - "
                "consider optimization or separation"
            )
        
        return recommendations


class ResourcePredictor:
    """Main resource prediction and allocation system"""
    
    def __init__(self):
        self.port_allocator = PortAllocator()
        self.resource_estimator = ResourceEstimator()
        self.allocated_resources: Dict[str, List[AllocatedResource]] = {}
        self.system_profiles: Dict[str, SystemResourceProfile] = {}
        self.metrics_collector = get_metrics_collector("resource_predictor")
        self.tracer = get_tracer("resource_predictor")
        self._lock = threading.RLock()
    
    def predict_system_resources(self, system_blueprint: ParsedSystemBlueprint) -> SystemResourceProfile:
        """Predict and allocate resources for an entire system"""
        with self.tracer.span("predict_system_resources") as span_id:
            logger.info(f"Predicting resources for system: {system_blueprint.system.name}")
            
            # Estimate base resource requirements
            resource_profile = self.resource_estimator.estimate_system_resources(system_blueprint)
            
            # Allocate ports for components
            port_requirements = self._generate_port_requirements(system_blueprint)
            allocated_ports = []
            
            for requirement in port_requirements:
                allocated_port = self.port_allocator.allocate_port(requirement)
                if allocated_port:
                    allocated_ports.append(allocated_port)
                else:
                    resource_profile.resource_conflicts.append(
                        f"Failed to allocate {requirement.port_type.value} port for {requirement.component_name}"
                    )
            
            resource_profile.allocated_ports = allocated_ports
            
            # Check for resource conflicts and add recommendations
            conflicts = self._detect_resource_conflicts(resource_profile)
            resource_profile.resource_conflicts.extend(conflicts)
            
            # Store system profile
            with self._lock:
                self.system_profiles[system_blueprint.system.name] = resource_profile
            
            self.metrics_collector.record_business_event("system_resources_predicted", 1)
            logger.info(f"Resource prediction completed for {system_blueprint.system.name}")
            
            return resource_profile
    
    def _generate_port_requirements(self, system_blueprint: ParsedSystemBlueprint) -> List[PortRequirement]:
        """Generate port requirements for system components"""
        port_requirements = []
        
        for component in system_blueprint.system.components:
            component_requirements = self._get_component_port_requirements(component)
            port_requirements.extend(component_requirements)
        
        return port_requirements
    
    def _get_component_port_requirements(self, component: ParsedComponent) -> List[PortRequirement]:
        """Get port requirements for a specific component"""
        requirements = []
        component_name = component.name
        component_type = component.type
        
        # Standard port requirements based on component type
        if component_type == "APIEndpoint":
            requirements.append(PortRequirement(
                port_type=PortType.HTTP,
                component_name=component_name,
                service_name="api",
                external_access=True,
                description="Main API endpoint"
            ))
            
            requirements.append(PortRequirement(
                port_type=PortType.HEALTH_CHECK,
                component_name=component_name,
                service_name="health",
                external_access=False,
                description="Health check endpoint"
            ))
        
        elif component_type == "Store":
            requirements.append(PortRequirement(
                port_type=PortType.DATABASE,
                component_name=component_name,
                service_name="database",
                external_access=False,
                description="Database connection"
            ))
        
        elif component_type in ["Source", "Transformer", "Sink"]:
            requirements.append(PortRequirement(
                port_type=PortType.METRICS,
                component_name=component_name,
                service_name="metrics",
                external_access=False,
                description="Component metrics"
            ))
        
        # Add admin port for complex components
        if component_type in ["APIEndpoint", "Store", "Model"]:
            requirements.append(PortRequirement(
                port_type=PortType.ADMIN,
                component_name=component_name,
                service_name="admin",
                external_access=False,
                description="Administrative interface"
            ))
        
        return requirements
    
    def _detect_resource_conflicts(self, profile: SystemResourceProfile) -> List[str]:
        """Detect potential resource conflicts"""
        conflicts = []
        
        # Check system resource limits
        try:
            system_memory = psutil.virtual_memory().total / (1024 * 1024)  # MB
            system_cpu_count = psutil.cpu_count()
            
            if profile.estimated_memory_mb > system_memory * 0.8:
                conflicts.append(
                    f"Memory requirement ({profile.estimated_memory_mb}MB) exceeds 80% of system memory ({system_memory:.0f}MB)"
                )
            
            if profile.estimated_cpu_percent > system_cpu_count * 50:
                conflicts.append(
                    f"CPU requirement ({profile.estimated_cpu_percent}%) may overwhelm system with {system_cpu_count} cores"
                )
        
        except Exception as e:
            logger.warning(f"Could not check system resources: {e}")
        
        # Check for port conflicts between external services
        external_ports = [
            port.port for port in profile.allocated_ports 
            if port.external_access
        ]
        
        if len(external_ports) != len(set(external_ports)):
            conflicts.append("Port conflicts detected between externally accessible services")
        
        return conflicts
    
    def get_system_resource_summary(self, system_name: str) -> Optional[Dict[str, Any]]:
        """Get resource summary for a system"""
        with self._lock:
            if system_name not in self.system_profiles:
                return None
            
            profile = self.system_profiles[system_name]
            port_summary = self.port_allocator.get_port_allocation_summary()
            
            return {
                "system_name": profile.system_name,
                "resource_estimates": {
                    "memory_mb": profile.estimated_memory_mb,
                    "cpu_percent": profile.estimated_cpu_percent,
                    "disk_mb": profile.estimated_disk_mb,
                    "network_mbps": profile.estimated_network_mbps
                },
                "port_allocations": [
                    {
                        "port": port.port,
                        "type": port.port_type.value,
                        "component": port.component_name,
                        "service": port.service_name,
                        "external": port.external_access
                    }
                    for port in profile.allocated_ports
                ],
                "conflicts": profile.resource_conflicts,
                "recommendations": profile.optimization_recommendations,
                "total_components": profile.total_components
            }
    
    def optimize_resource_allocation(self, system_name: str) -> Dict[str, Any]:
        """Optimize resource allocation for a system"""
        with self.tracer.span("optimize_resource_allocation") as span_id:
            with self._lock:
                if system_name not in self.system_profiles:
                    return {"error": "System not found"}
                
                profile = self.system_profiles[system_name]
                optimizations = []
                
                # Port optimization
                external_ports = [p for p in profile.allocated_ports if p.external_access]
                if len(external_ports) > 1:
                    # Group external services on adjacent ports
                    optimizations.append("Consider using a reverse proxy to consolidate external access")
                
                # Memory optimization
                if profile.estimated_memory_mb > 2048:
                    optimizations.append("Consider implementing memory-mapped files for large data sets")
                    optimizations.append("Use object pooling for frequently allocated objects")
                
                # CPU optimization
                if profile.estimated_cpu_percent > 60:
                    optimizations.append("Implement async/await patterns for I/O-bound operations")
                    optimizations.append("Consider CPU affinity for compute-intensive components")
                
                # Network optimization
                if profile.estimated_network_mbps > 20:
                    optimizations.append("Implement request batching and compression")
                    optimizations.append("Use connection multiplexing where possible")
                
                return {
                    "system_name": system_name,
                    "optimization_suggestions": optimizations,
                    "current_recommendations": profile.optimization_recommendations
                }
    
    def deallocate_system_resources(self, system_name: str) -> bool:
        """Deallocate all resources for a system"""
        with self._lock:
            if system_name not in self.system_profiles:
                return False
            
            profile = self.system_profiles[system_name]
            
            # Deallocate ports
            for allocated_port in profile.allocated_ports:
                self.port_allocator.deallocate_port(
                    allocated_port.component_name,
                    allocated_port.service_name
                )
            
            # Remove system profile
            del self.system_profiles[system_name]
            
            # Remove allocated resources
            if system_name in self.allocated_resources:
                del self.allocated_resources[system_name]
            
            logger.info(f"Deallocated all resources for system: {system_name}")
            self.metrics_collector.record_business_event("system_resources_deallocated", 1)
            
            return True
    
    def get_global_resource_usage(self) -> Dict[str, Any]:
        """Get global resource usage across all systems"""
        with self._lock:
            total_memory = sum(p.estimated_memory_mb for p in self.system_profiles.values())
            total_cpu = sum(p.estimated_cpu_percent for p in self.system_profiles.values())
            total_disk = sum(p.estimated_disk_mb for p in self.system_profiles.values())
            total_network = sum(p.estimated_network_mbps for p in self.system_profiles.values())
            
            all_ports = []
            for profile in self.system_profiles.values():
                all_ports.extend(profile.allocated_ports)
            
            port_summary = self.port_allocator.get_port_allocation_summary()
            
            return {
                "total_systems": len(self.system_profiles),
                "total_allocated_ports": len(all_ports),
                "aggregate_resources": {
                    "memory_mb": total_memory,
                    "cpu_percent": total_cpu,
                    "disk_mb": total_disk,
                    "network_mbps": total_network
                },
                "port_allocation_summary": port_summary,
                "active_systems": list(self.system_profiles.keys())
            }


# Global resource predictor instance
global_resource_predictor = ResourcePredictor()


def get_resource_predictor() -> ResourcePredictor:
    """Get the global resource predictor instance"""
    return global_resource_predictor


def predict_and_allocate_resources(system_blueprint: ParsedSystemBlueprint) -> SystemResourceProfile:
    """Convenience function to predict and allocate resources for a system"""
    return global_resource_predictor.predict_system_resources(system_blueprint)