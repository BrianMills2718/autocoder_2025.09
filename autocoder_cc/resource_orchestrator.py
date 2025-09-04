#!/usr/bin/env python3
"""
ResourceOrchestrator: Generation-time resource allocation for Autocoder 3.3

Handles allocation of shared system resources (ports, database names, topics)
to prevent conflicts in multi-component systems. Runs after component generation
but before system assembly.

Key Features:
- Scans generated components for resource requirements
- Uses centralized PortRegistry for thread-safe port allocation
- Generates deterministic resource manifest
- Injects allocations into system config

Phase 2A Enhancement: Integrated with centralized port management
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
import re
import yaml
import hashlib
import os
import json
import socket
import fcntl
import psutil
from datetime import datetime, timedelta

# Phase 2A: Import centralized port registry
from autocoder_cc.core.port_registry import get_port_registry


class ResourceType(Enum):
    NETWORK_PORT = "network_port"
    DATABASE_NAME = "database_name"
    DATABASE_CONNECTION = "database_connection"
    MESSAGE_TOPIC = "message_topic"
    MESSAGE_QUEUE = "message_queue"
    STORAGE_PATH = "storage_path"
    STORAGE_VOLUME = "storage_volume"
    CACHE_KEY_PREFIX = "cache_key_prefix"


@dataclass
class ResourceRequirement:
    component_name: str
    component_type: str
    resource_type: ResourceType
    hint: Optional[str] = None  # From blueprint
    priority: int = 0  # Higher priority gets first pick


@dataclass
class ResourceAllocation:
    component_name: str
    resource_type: ResourceType
    allocated_value: Any
    source: str  # "pool", "hint", "pattern"


@dataclass
class ResourceManifest:
    system_name: str
    allocations: List[ResourceAllocation]
    metadata: Dict[str, Any]


@dataclass
class PortAllocation:
    port: int
    system: str
    component: str
    pid: int
    timestamp: str


class PortAllocator:
    """
    Production-grade port allocation system with conflict resolution and process management.
    
    Features:
    - File-based locking for concurrent access
    - Process validation for stale entry cleanup
    - Deterministic allocation with conflict resolution
    - Environment-configurable port ranges
    """
    
    def __init__(self):
        self.port_range = self._get_port_range()
        self.state_file = Path(os.getenv('AUTOCODER_PORT_STATE_FILE', '~/.autocoder/allocated_ports.json')).expanduser()
        self.max_attempts = int(os.getenv('AUTOCODER_PORT_ATTEMPTS', '50'))
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _get_port_range(self) -> tuple[int, int]:
        range_str = os.getenv('AUTOCODER_PORT_RANGE', '8000-18000')
        start, end = map(int, range_str.split('-'))
        return start, end
    
    def allocate_port(self, system: str, component: str) -> int:
        """Allocate a unique port for the given system component"""
        low, high = self.port_range
        span = high - low + 1
        
        # 1. Deterministic first guess
        seed = f"{system}_{component}"
        first_guess = low + (int(hashlib.md5(seed.encode()).hexdigest(), 16) % span)
        
        # 2. Try to reserve it with conflict resolution
        for i in range(self.max_attempts):
            candidate_port = low + ((first_guess - low + i) % span)
            
            if self._is_port_free(candidate_port) and self._reserve_port(candidate_port, system, component):
                return candidate_port
        
        raise RuntimeError(f"Port allocation exhausted after {self.max_attempts} attempts in range {low}-{high}")
    
    def _is_port_free(self, port: int) -> bool:
        """Check if port is available by attempting to bind"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
                sock.bind(('', port))
                return True
        except OSError:
            return False
    
    def _reserve_port(self, port: int, system: str, component: str) -> bool:
        """Reserve port in host-level registry with file locking"""
        try:
            # Cleanup stale entries first
            self._cleanup_stale_entries()
            
            with open(self.state_file, 'a+') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                f.seek(0)
                
                # Load existing allocations
                try:
                    data = json.load(f) if f.read() else {"ports": {}, "last_cleanup": datetime.utcnow().isoformat()}
                except json.JSONDecodeError:
                    data = {"ports": {}, "last_cleanup": datetime.utcnow().isoformat()}
                
                # Check if port already allocated
                if str(port) in data["ports"]:
                    existing = data["ports"][str(port)]
                    # If same system/component, allow (restart scenario)
                    if existing["system"] == system and existing["component"] == component:
                        return True
                    return False
                
                # Reserve the port
                data["ports"][str(port)] = {
                    "system": system,
                    "component": component,
                    "pid": os.getpid(),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Write back
                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=2)
                return True
                
        except Exception as e:
            print(f"Warning: Port reservation failed: {e}")
            return False
    
    def _cleanup_stale_entries(self):
        """Remove entries for dead processes or old timestamps"""
        if not self.state_file.exists():
            return
            
        try:
            with open(self.state_file, 'r+') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                data = json.load(f)
                
                # Clean up entries
                current_time = datetime.utcnow()
                ports_to_remove = []
                
                for port, allocation in data["ports"].items():
                    # Remove if process dead
                    if not psutil.pid_exists(allocation["pid"]):
                        ports_to_remove.append(port)
                        continue
                    
                    # Remove if older than 7 days
                    alloc_time = datetime.fromisoformat(allocation["timestamp"])
                    if current_time - alloc_time > timedelta(days=7):
                        ports_to_remove.append(port)
                
                # Remove stale entries
                for port in ports_to_remove:
                    del data["ports"][port]
                
                data["last_cleanup"] = current_time.isoformat()
                
                # Write back
                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Cleanup failed: {e}")


class ResourceOrchestrator:
    """
    Manages allocation of shared system resources during generation.
    
    Process:
    1. Scan components for resource requirements
    2. Allocate from managed pools/patterns
    3. Generate resource manifest
    4. Create configuration files
    """
    
    def __init__(self, port_range: tuple = None, 
                 database_prefix: str = None,
                 storage_base_path: str = None):
        # Use environment variable or sensible defaults for port range
        if port_range is None:
            # Check environment variables for custom port range
            port_start = int(os.environ.get('AUTOCODER_PORT_START', '8000'))
            port_end = int(os.environ.get('AUTOCODER_PORT_END', '18000'))  # Expanded default range
            self.port_range = (port_start, port_end)
        else:
            self.port_range = port_range
        
        # Resource allocation state
        self.allocated_ports: Set[int] = set()
        self.allocated_databases: Set[str] = set()
        self.allocated_queues: Set[str] = set()
        self.allocated_storage: Set[str] = set()
        
        # Configuration for resource allocation
        self.database_prefix = database_prefix or os.environ.get('AUTOCODER_DB_PREFIX', 'autocoder')
        self.storage_base_path = storage_base_path or os.environ.get('AUTOCODER_STORAGE_BASE', '/var/lib/autocoder/storage')
        
        # Initialize single PortAllocator instance for efficient reuse
        self.port_allocator = PortAllocator()
        
    def allocate_port(self, component_name: str, system_name: str) -> int:
        """
        Public API for port allocation using centralized PortRegistry.
        
        Phase 2A Enhancement: Uses centralized port registry for thread-safe allocation
        
        Args:
            component_name: Name of the component requesting a port
            system_name: Name of the system the component belongs to
            
        Returns:
            Allocated port number
            
        Raises:
            RuntimeError: If port allocation fails
        """
        try:
            # Use centralized port registry instead of local port allocator
            port_registry = get_port_registry()
            
            # Determine component type for optimized port range
            component_type = self._determine_component_type(component_name)
            
            port = port_registry.allocate_port(
                component_name=component_name,
                component_type=component_type,
                system_id=system_name
            )
            
            self.allocated_ports.add(port)
            return port
        except RuntimeError as e:
            raise RuntimeError(f"Port allocation failed for component '{component_name}' in system '{system_name}': {e}")
    
    def _determine_component_type(self, component_name: str) -> Optional[str]:
        """
        Determine component type from component name for optimized port allocation
        
        Args:
            component_name: Name of the component
            
        Returns:
            Component type string or None
        """
        # Common component type patterns
        if 'api' in component_name.lower() or 'endpoint' in component_name.lower():
            return 'APIEndpoint'
        elif 'websocket' in component_name.lower() or 'ws' in component_name.lower():
            return 'WebSocket'
        elif 'store' in component_name.lower() or 'db' in component_name.lower():
            return 'Store'
        elif 'controller' in component_name.lower():
            return 'Controller'
        else:
            return None
    
    def scan_components(self, component_dir: Path) -> List[ResourceRequirement]:
        """
        Scan generated component files to identify resource requirements.
        
        Looks for:
        - APIEndpoint components needing ports
        - Store components needing database names
        - StreamProcessor components needing topics
        """
        requirements = []
        
        if not component_dir.exists():
            return requirements
            
        for component_file in component_dir.glob("*.py"):
            if component_file.name == "__init__.py":
                continue
                
            component_name = component_file.stem
            content = component_file.read_text()
            
            # Detect component type from class inheritance
            component_type = self._detect_component_type(content)
            
            if component_type == "APIEndpoint":
                requirements.append(ResourceRequirement(
                    component_name=component_name,
                    component_type=component_type,
                    resource_type=ResourceType.NETWORK_PORT,
                    priority=1
                ))
                
            elif component_type == "Store":
                # Store components need database name and connection
                requirements.extend([
                    ResourceRequirement(
                        component_name=component_name,
                        component_type=component_type,
                        resource_type=ResourceType.DATABASE_NAME,
                        priority=2
                    ),
                    ResourceRequirement(
                        component_name=component_name,
                        component_type=component_type,
                        resource_type=ResourceType.DATABASE_CONNECTION,
                        priority=2
                    )
                ])
                
            elif component_type == "StreamProcessor":
                # Stream processors need topics and might need queues
                requirements.append(ResourceRequirement(
                    component_name=component_name,
                    component_type=component_type,
                    resource_type=ResourceType.MESSAGE_TOPIC,
                    priority=3
                ))
                
            elif component_type == "Source":
                # Sources might need storage for buffering
                requirements.append(ResourceRequirement(
                    component_name=component_name,
                    component_type=component_type,
                    resource_type=ResourceType.STORAGE_PATH,
                    priority=4
                ))
                
            elif component_type == "Accumulator":
                # Accumulators typically need cache/storage
                requirements.extend([
                    ResourceRequirement(
                        component_name=component_name,
                        component_type=component_type,
                        resource_type=ResourceType.CACHE_KEY_PREFIX,
                        priority=3
                    ),
                    ResourceRequirement(
                        component_name=component_name,
                        component_type=component_type,
                        resource_type=ResourceType.STORAGE_VOLUME,
                        priority=4
                    )
                ])
                
            elif component_type == "Controller":
                # Controllers need message queues for coordination
                requirements.append(ResourceRequirement(
                    component_name=component_name,
                    component_type=component_type,
                    resource_type=ResourceType.MESSAGE_QUEUE,
                    priority=3
                ))
                
            elif component_type == "Sink":
                # Sinks might need storage for output
                requirements.append(ResourceRequirement(
                    component_name=component_name,
                    component_type=component_type,
                    resource_type=ResourceType.STORAGE_PATH,
                    priority=4
                ))
                
            # Check for additional resource hints in component code
            requirements.extend(self._extract_resource_hints(content, component_name, component_type))
                
        return requirements
    
    def _detect_component_type(self, content: str) -> str:
        """Detect component type from class inheritance patterns."""
        inheritance_patterns = {
            "APIEndpoint": r"class\s+\w+\(APIEndpoint\)",
            "Store": r"class\s+\w+\(Store\)",
            "StreamProcessor": r"class\s+\w+\(StreamProcessor\)",
            "Source": r"class\s+\w+\(Source\)",
            "Transformer": r"class\s+\w+\(Transformer\)",
            "Model": r"class\s+\w+\(Model\)",
            "Accumulator": r"class\s+\w+\(Accumulator\)",
            "Controller": r"class\s+\w+\(Controller\)",
            "Sink": r"class\s+\w+\(Sink\)",
            "Router": r"class\s+\w+\(Router\)"
        }
        
        for component_type, pattern in inheritance_patterns.items():
            if re.search(pattern, content):
                return component_type
                
        return "Unknown"
    
    def _extract_resource_hints(self, content: str, component_name: str, component_type: str) -> List[ResourceRequirement]:
        """Extract additional resource requirements from component code patterns."""
        requirements = []
        
        # Look for database patterns
        db_patterns = [
            r'psycopg2|postgresql|postgres',
            r'mysql|pymysql',
            r'sqlite',
            r'redis.*connection',
            r'database.*pool'
        ]
        
        for pattern in db_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                requirements.append(ResourceRequirement(
                    component_name=component_name,
                    component_type=component_type,
                    resource_type=ResourceType.DATABASE_CONNECTION,
                    priority=2,
                    hint=f"detected_{pattern.split('|')[0]}"
                ))
                break
        
        # Look for message queue patterns
        mq_patterns = [
            r'kafka|KafkaProducer|KafkaConsumer',
            r'rabbitmq|pika|amqp',
            r'redis.*pubsub|redis.*channel',
            r'queue\.Queue|asyncio\.Queue'
        ]
        
        for pattern in mq_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                requirements.append(ResourceRequirement(
                    component_name=component_name,
                    component_type=component_type,
                    resource_type=ResourceType.MESSAGE_QUEUE,
                    priority=3,
                    hint=f"detected_{pattern.split('|')[0]}"
                ))
                break
        
        # Look for storage patterns
        storage_patterns = [
            r'open\s*\(.*["\']w["\']',  # File writing
            r'pathlib\.Path|os\.path',
            r'shutil\.|tempfile\.',
            r'Volume|PersistentVolume',
            r'aws.*s3|boto3',
            r'azure.*storage|gcs'
        ]
        
        for pattern in storage_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                requirements.append(ResourceRequirement(
                    component_name=component_name,
                    component_type=component_type,
                    resource_type=ResourceType.STORAGE_VOLUME,
                    priority=4,
                    hint=f"detected_storage"
                ))
                break
        
        return requirements
    
    def allocate_resources(self, requirements: List[ResourceRequirement], 
                          system_name: str) -> ResourceManifest:
        """
        Allocate resources from managed pools according to requirements.
        
        Allocation Rules:
        - No conflicts within system
        - Deterministic assignment (same input = same output)
        - Respect blueprint hints where possible
        - Priority-based allocation order
        """
        allocations = []
        
        # Sort by priority (higher first)
        sorted_requirements = sorted(requirements, key=lambda r: r.priority)
        
        for req in sorted_requirements:
            allocation = self._allocate_single_resource(req, system_name)
            if allocation:
                allocations.append(allocation)
                
        return ResourceManifest(
            system_name=system_name,
            allocations=allocations,
            metadata={
                "generated_by": "ResourceOrchestrator",
                "allocation_strategy": "deterministic_pool",
                "port_range": self.port_range
            }
        )
    
    def _allocate_single_resource(self, req: ResourceRequirement, 
                                 system_name: str) -> Optional[ResourceAllocation]:
        """Allocate a single resource based on type and requirements."""
        
        if req.resource_type == ResourceType.NETWORK_PORT:
            port = self.allocate_port(req.component_name, system_name)
            if port:
                return ResourceAllocation(
                    component_name=req.component_name,
                    resource_type=req.resource_type,
                    allocated_value=port,
                    source="pool"
                )
                
        elif req.resource_type == ResourceType.DATABASE_NAME:
            db_name = self._allocate_database_name(req.component_name, system_name)
            return ResourceAllocation(
                component_name=req.component_name,
                resource_type=req.resource_type,
                allocated_value=db_name,
                source="pattern"
            )
            
        elif req.resource_type == ResourceType.DATABASE_CONNECTION:
            connection_string = self._allocate_database_connection(req.component_name, system_name, req.hint)
            return ResourceAllocation(
                component_name=req.component_name,
                resource_type=req.resource_type,
                allocated_value=connection_string,
                source="generated"
            )
            
        elif req.resource_type == ResourceType.MESSAGE_TOPIC:
            topic_name = self._allocate_message_topic(req.component_name, system_name)
            return ResourceAllocation(
                component_name=req.component_name,
                resource_type=req.resource_type,
                allocated_value=topic_name,
                source="pattern"
            )
            
        elif req.resource_type == ResourceType.MESSAGE_QUEUE:
            queue_name = self._allocate_message_queue(req.component_name, system_name, req.hint)
            return ResourceAllocation(
                component_name=req.component_name,
                resource_type=req.resource_type,
                allocated_value=queue_name,
                source="pattern"
            )
            
        elif req.resource_type == ResourceType.STORAGE_PATH:
            storage_path = self._allocate_storage_path(req.component_name, system_name)
            return ResourceAllocation(
                component_name=req.component_name,
                resource_type=req.resource_type,
                allocated_value=storage_path,
                source="pattern"
            )
            
        elif req.resource_type == ResourceType.STORAGE_VOLUME:
            volume_name = self._allocate_storage_volume(req.component_name, system_name)
            return ResourceAllocation(
                component_name=req.component_name,
                resource_type=req.resource_type,
                allocated_value=volume_name,
                source="pattern"
            )
            
        elif req.resource_type == ResourceType.CACHE_KEY_PREFIX:
            key_prefix = self._allocate_cache_key_prefix(req.component_name, system_name)
            return ResourceAllocation(
                component_name=req.component_name,
                resource_type=req.resource_type,
                allocated_value=key_prefix,
                source="pattern"
            )
            
        return None
    
    def _allocate_port(self, component_name: str, system_name: str) -> Optional[int]:
        """
        Allocate a unique port using the reusable PortAllocator instance.
        
        This delegates to the enhanced PortAllocator for production-grade
        port management with file locking and process validation.
        """
        try:
            port = self.port_allocator.allocate_port(system_name, component_name)
            self.allocated_ports.add(port)
            return port
        except RuntimeError as e:
            print(f"Port allocation failed: {e}")
            return None
    
    def _allocate_database_name(self, component_name: str, system_name: str) -> str:
        """Allocate a unique database name."""
        db_name = f"{self.database_prefix}_{system_name}_{component_name}_db"
        # Ensure unique database name
        if db_name in self.allocated_databases:
            counter = 1
            while f"{db_name}_{counter}" in self.allocated_databases:
                counter += 1
            db_name = f"{db_name}_{counter}"
        
        self.allocated_databases.add(db_name)
        return db_name
    
    def _allocate_database_connection(self, component_name: str, system_name: str, hint: Optional[str] = None) -> str:
        """Generate a database connection string based on detected database type."""
        db_name = self._allocate_database_name(component_name, system_name)
        
        # Determine database type from hint
        if hint and "postgres" in hint:
            return f"postgresql://{system_name}_user:${{{component_name.upper()}_DB_PASSWORD}}@postgres:5432/{db_name}"
        elif hint and "mysql" in hint:
            return f"mysql://{system_name}_user:${{{component_name.upper()}_DB_PASSWORD}}@mysql:3306/{db_name}"
        elif hint and "redis" in hint:
            return f"redis://:{{{component_name.upper()}_REDIS_PASSWORD}}@redis:6379/{hash(db_name) % 16}"
        elif hint and "sqlite" in hint:
            return f"sqlite:///{self.storage_base_path}/{system_name}/{db_name}.db"
        else:
            # Default to PostgreSQL
            return f"postgresql://{system_name}_user:${{{component_name.upper()}_DB_PASSWORD}}@postgres:5432/{db_name}"
    
    def _allocate_message_topic(self, component_name: str, system_name: str) -> str:
        """Allocate a unique message topic name."""
        topic_name = f"{system_name}.{component_name}.events"
        # Ensure unique topic name
        if topic_name in self.allocated_queues:
            counter = 1
            while f"{topic_name}.{counter}" in self.allocated_queues:
                counter += 1
            topic_name = f"{topic_name}.{counter}"
        
        self.allocated_queues.add(topic_name)
        return topic_name
    
    def _allocate_message_queue(self, component_name: str, system_name: str, hint: Optional[str] = None) -> str:
        """Allocate a message queue name based on detected queue type."""
        base_name = f"{system_name}.{component_name}.queue"
        
        # Determine queue type from hint
        if hint and "kafka" in hint:
            queue_name = f"{base_name}.kafka"
        elif hint and "rabbitmq" in hint:
            queue_name = f"{base_name}.rabbitmq"
        elif hint and "redis" in hint:
            queue_name = f"{base_name}.redis"
        else:
            # Default to generic queue
            queue_name = base_name
        
        # Ensure unique queue name
        if queue_name in self.allocated_queues:
            counter = 1
            while f"{queue_name}.{counter}" in self.allocated_queues:
                counter += 1
            queue_name = f"{queue_name}.{counter}"
        
        self.allocated_queues.add(queue_name)
        return queue_name
    
    def _allocate_storage_path(self, component_name: str, system_name: str) -> str:
        """Allocate a unique storage path."""
        storage_path = f"{self.storage_base_path}/{system_name}/{component_name}"
        
        # Ensure unique storage path
        if storage_path in self.allocated_storage:
            counter = 1
            while f"{storage_path}_{counter}" in self.allocated_storage:
                counter += 1
            storage_path = f"{storage_path}_{counter}"
        
        self.allocated_storage.add(storage_path)
        return storage_path
    
    def _allocate_storage_volume(self, component_name: str, system_name: str) -> str:
        """Allocate a unique storage volume name for Kubernetes/Docker."""
        volume_name = f"{system_name}-{component_name}-volume"
        
        # Ensure unique volume name
        if volume_name in self.allocated_storage:
            counter = 1
            while f"{volume_name}-{counter}" in self.allocated_storage:
                counter += 1
            volume_name = f"{volume_name}-{counter}"
        
        self.allocated_storage.add(volume_name)
        return volume_name
    
    def _allocate_cache_key_prefix(self, component_name: str, system_name: str) -> str:
        """Allocate a unique cache key prefix."""
        key_prefix = f"{system_name}:{component_name}:"
        
        # Ensure unique key prefix
        if key_prefix in self.allocated_storage:
            counter = 1
            while f"{system_name}:{component_name}_{counter}:" in self.allocated_storage:
                counter += 1
            key_prefix = f"{system_name}:{component_name}_{counter}:"
        
        self.allocated_storage.add(key_prefix)
        return key_prefix
    
    def generate_config(self, manifest: ResourceManifest) -> Dict[str, Any]:
        """
        Generate system configuration from resource manifest.
        
        Creates config.yaml structure that components can read at runtime.
        """
        config = {
            "system": {
                "name": manifest.system_name,
                "version": "1.0.0"
            },
            "components": {},
            "resources": {
                "metadata": {
                    "generated_by": manifest.metadata.get("generated_by"),
                    "allocation_strategy": manifest.metadata.get("allocation_strategy"),
                    "port_range": list(manifest.metadata.get("port_range", self.port_range))
                }
            }
        }
        
        # Group allocations by component
        for allocation in manifest.allocations:
            component_name = allocation.component_name
            
            if component_name not in config["components"]:
                config["components"][component_name] = {}
                
            # Add resource allocation
            if allocation.resource_type == ResourceType.NETWORK_PORT:
                config["components"][component_name]["port"] = allocation.allocated_value
            elif allocation.resource_type == ResourceType.DATABASE_NAME:
                config["components"][component_name]["database_name"] = allocation.allocated_value
            elif allocation.resource_type == ResourceType.DATABASE_CONNECTION:
                config["components"][component_name]["database_connection"] = allocation.allocated_value
            elif allocation.resource_type == ResourceType.MESSAGE_TOPIC:
                config["components"][component_name]["message_topic"] = allocation.allocated_value
            elif allocation.resource_type == ResourceType.MESSAGE_QUEUE:
                config["components"][component_name]["message_queue"] = allocation.allocated_value
            elif allocation.resource_type == ResourceType.STORAGE_PATH:
                config["components"][component_name]["storage_path"] = allocation.allocated_value
            elif allocation.resource_type == ResourceType.STORAGE_VOLUME:
                config["components"][component_name]["storage_volume"] = allocation.allocated_value
            elif allocation.resource_type == ResourceType.CACHE_KEY_PREFIX:
                config["components"][component_name]["cache_key_prefix"] = allocation.allocated_value
                
        return config
    
    def allocate_ports(self, component_names: List[str]) -> Dict[str, int]:
        """
        Allocate ports for a list of components.
        
        This is a convenience method matching the interface expected in CLAUDE.md.
        
        Args:
            component_names: List of component names needing ports
            
        Returns:
            Dict mapping component name to allocated port
        """
        system_name = "default_system"  # Use default if not provided
        port_allocations = {}
        
        for component_name in component_names:
            port = self.allocate_port(component_name, system_name)
            if port:
                port_allocations[component_name] = port
            else:
                raise ValueError(f"Unable to allocate port for {component_name} - port pool exhausted")
                
        return port_allocations
    
    def cleanup_system_resources(self, system_name: str) -> Dict[str, int]:
        """
        Clean up all allocated resources for a system using centralized registry.
        
        Phase 2A Enhancement: Implements port cleanup on system generation failure
        
        Args:
            system_name: Name of the system to clean up
            
        Returns:
            Dict with cleanup statistics
        """
        port_registry = get_port_registry()
        
        # Clean up ports from centralized registry
        ports_deallocated = port_registry.cleanup_system(system_name)
        
        # Update local tracking
        system_ports = port_registry.get_system_ports(system_name)
        for port in system_ports:
            self.allocated_ports.discard(port)
        
        cleanup_stats = {
            'ports_deallocated': ports_deallocated,
            'system_id': system_name
        }
        
        return cleanup_stats
    
    def validate_port_availability(self, required_ports: List[int]) -> Dict[str, List[int]]:
        """
        Validate availability of specific ports using centralized registry.
        
        Phase 2A Enhancement: Port availability validation
        
        Args:
            required_ports: List of port numbers to validate
            
        Returns:
            Dict with 'available' and 'unavailable' port lists
        """
        port_registry = get_port_registry()
        available, unavailable = port_registry.validate_port_availability(required_ports)
        
        return {
            'available': available,
            'unavailable': unavailable
        }
    
    def write_config_file(self, config: Dict[str, Any], output_path: Path) -> None:
        """Write configuration to YAML file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
    
    def generate_deployment_manifests(self, manifest: ResourceManifest, 
                                    output_dir: Path) -> None:
        """
        Generate deployment manifests with correct resource mappings.
        
        Updates docker-compose.yml and kubernetes manifests with allocated ports.
        """
        # Update docker-compose.yml
        self._update_docker_compose(manifest, output_dir)
        
        # Could extend for Kubernetes, Terraform, etc.
    
    def _update_docker_compose(self, manifest: ResourceManifest, output_dir: Path) -> None:
        """Update docker-compose.yml with allocated ports."""
        compose_file = output_dir / "docker-compose.yml"
        
        if not compose_file.exists():
            return
            
        try:
            with open(compose_file, 'r') as f:
                compose_data = yaml.safe_load(f) or {}
                
            # Update port mappings for API components
            services = compose_data.get('services', {})
            
            for allocation in manifest.allocations:
                if allocation.resource_type == ResourceType.NETWORK_PORT:
                    component_name = allocation.component_name
                    port = allocation.allocated_value
                    
                    if component_name in services:
                        # Map external port to internal port
                        services[component_name]['ports'] = [f"{port}:{port}"]
                        
            with open(compose_file, 'w') as f:
                yaml.dump(compose_data, f, default_flow_style=False, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not update docker-compose.yml: {e}")


def main():
    """CLI interface for testing ResourceOrchestrator."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python resource_orchestrator.py <component_dir> [system_name]")
        sys.exit(1)
        
    component_dir = Path(sys.argv[1])
    system_name = sys.argv[2] if len(sys.argv) > 2 else "test_system"
    
    orchestrator = ResourceOrchestrator()
    
    # Scan for requirements
    requirements = orchestrator.scan_components(component_dir)
    print(f"Found {len(requirements)} resource requirements:")
    for req in requirements:
        print(f"  - {req.component_name} ({req.component_type}): {req.resource_type.value}")
    
    # Allocate resources
    manifest = orchestrator.allocate_resources(requirements, system_name)
    print(f"\nAllocated {len(manifest.allocations)} resources:")
    for alloc in manifest.allocations:
        print(f"  - {alloc.component_name}: {alloc.resource_type.value} = {alloc.allocated_value}")
    
    # Generate config
    config = orchestrator.generate_config(manifest)
    print(f"\nGenerated configuration:")
    print(yaml.dump(config, default_flow_style=False, indent=2))


if __name__ == "__main__":
    main()