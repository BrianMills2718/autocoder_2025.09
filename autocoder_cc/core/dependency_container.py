#!/usr/bin/env python3
"""
Enhanced Dependency Container for Autocoder CC

Provides centralized dependency injection with interface-based registration,
lifecycle management, circular dependency detection, and visualization.
"""
import logging
from typing import Dict, Any, Type, TypeVar, Optional, Callable, List, Set, Union
from abc import ABC, abstractmethod
import inspect
from collections import defaultdict
import weakref
from enum import Enum
from datetime import datetime
import threading
from contextlib import contextmanager
import json
from dataclasses import dataclass, field
import time

from autocoder_cc.observability import get_logger, get_metrics_collector, get_tracer


T = TypeVar('T')


class Lifecycle(Enum):
    """Dependency lifecycle management options"""
    SINGLETON = "singleton"      # One instance for entire application
    TRANSIENT = "transient"      # New instance per request
    SCOPED = "scoped"           # One instance per scope/context


@dataclass
class DependencyMetadata:
    """Metadata for dependency registration"""
    registered_at: datetime = field(default_factory=datetime.now)
    resolution_count: int = 0
    last_resolved_at: Optional[datetime] = None
    average_resolution_time_ms: float = 0.0
    tags: List[str] = field(default_factory=list)
    description: Optional[str] = None


class DependencyScope:
    """Manages scoped dependencies"""
    def __init__(self, name: str):
        self.name = name
        self.instances: Dict[str, Any] = {}
        self.created_at = datetime.now()
        self.resolution_count = 0
        
    def get_or_create(self, key: str, factory: Callable) -> Any:
        """Get existing instance or create new one in scope"""
        if key not in self.instances:
            self.instances[key] = factory()
        self.resolution_count += 1
        return self.instances[key]
    
    def clear(self):
        """Clear all instances in scope"""
        self.instances.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scope statistics"""
        return {
            "name": self.name,
            "instance_count": len(self.instances),
            "resolution_count": self.resolution_count,
            "created_at": self.created_at.isoformat(),
            "age_seconds": (datetime.now() - self.created_at).total_seconds()
        }


class DependencyRegistration:
    """Represents a registered dependency"""
    def __init__(
        self,
        interface: Type,
        implementation: Type,
        factory: Optional[Callable] = None,
        lifecycle: Lifecycle = Lifecycle.SINGLETON,
        metadata: Optional[DependencyMetadata] = None
    ):
        self.interface = interface
        self.implementation = implementation
        self.factory = factory
        self.lifecycle = lifecycle
        self.metadata = metadata or DependencyMetadata()
        self.instance = None  # For singletons
        self.dependencies: List[Type] = []  # Extracted dependencies
        self._extract_dependencies()
        
    def _extract_dependencies(self):
        """Extract constructor dependencies for graph analysis"""
        if not self.implementation:
            return
            
        try:
            sig = inspect.signature(self.implementation.__init__)
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                    
                if param.annotation != inspect.Parameter.empty:
                    dep_type = param.annotation
                    # Handle Optional, List, etc.
                    if hasattr(dep_type, '__origin__'):
                        if hasattr(dep_type, '__args__'):
                            dep_type = dep_type.__args__[0]
                    
                    if inspect.isclass(dep_type):
                        self.dependencies.append(dep_type)
        except Exception:
            # Some types might not have inspectable constructors
            pass
    
    def create_instance(self, container: 'EnhancedDependencyContainer') -> Any:
        """Create instance with dependency injection"""
        start_time = time.time()
        
        try:
            if self.factory:
                instance = self.factory(container)
            else:
                # Extract constructor dependencies
                sig = inspect.signature(self.implementation.__init__)
                kwargs = {}
                
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                        
                    # Get type hint for dependency resolution
                    if param.annotation != inspect.Parameter.empty:
                        dep_type = param.annotation
                        
                        # Handle Optional types
                        if hasattr(dep_type, '__origin__'):
                            if dep_type.__origin__ is Union:
                                # Get first non-None type from Optional
                                args = [t for t in dep_type.__args__ if t is not type(None)]
                                if args:
                                    dep_type = args[0]
                            else:
                                dep_type = dep_type.__origin__
                        
                        # Resolve dependency
                        if inspect.isclass(dep_type) and container.has_registration(dep_type):
                            kwargs[param_name] = container.resolve(dep_type)
                        elif param.default == inspect.Parameter.empty:
                            raise ValueError(
                                f"Cannot resolve required dependency {param_name}: {dep_type} "
                                f"for {self.implementation.__name__}"
                            )
                
                instance = self.implementation(**kwargs)
            
            # Update metadata
            elapsed_ms = (time.time() - start_time) * 1000
            self.metadata.resolution_count += 1
            self.metadata.last_resolved_at = datetime.now()
            
            # Update rolling average
            if self.metadata.average_resolution_time_ms == 0:
                self.metadata.average_resolution_time_ms = elapsed_ms
            else:
                self.metadata.average_resolution_time_ms = (
                    self.metadata.average_resolution_time_ms * 0.9 + elapsed_ms * 0.1
                )
            
            return instance
            
        except Exception as e:
            raise RuntimeError(
                f"Failed to create instance of {self.implementation.__name__}: {str(e)}"
            ) from e


class CircularDependencyError(Exception):
    """Raised when circular dependency is detected"""
    def __init__(self, cycle: List[str]):
        self.cycle = cycle
        super().__init__(f"Circular dependency detected: {' -> '.join(cycle)}")


class EnhancedDependencyContainer:
    """
    Enhanced dependency injection container with interface-based registration,
    lifecycle management, circular dependency detection, and visualization.
    """
    
    def __init__(self):
        self._registrations: Dict[Type, DependencyRegistration] = {}
        self._aliases: Dict[str, Type] = {}
        self._scopes: Dict[str, DependencyScope] = {}
        self._current_scope: Optional[str] = None
        self._resolution_stack: List[Type] = []
        self._lock = threading.RLock()
        
        # Performance tracking
        self._total_resolutions = 0
        self._total_resolution_time_ms = 0.0
        
        # Observability
        self.logger = get_logger(self.__class__.__name__)
        self.metrics = get_metrics_collector("dependency_container")
        self.tracer = get_tracer("dependency_container")
        
        self.logger.info("Enhanced dependency container initialized")
    
    def register(
        self,
        interface: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[Any], T]] = None,
        lifecycle: Lifecycle = Lifecycle.SINGLETON,
        tags: Optional[List[str]] = None,
        alias: Optional[str] = None,
        description: Optional[str] = None
    ) -> None:
        """
        Register a dependency with the container.
        
        Args:
            interface: The interface/abstract base class
            implementation: The concrete implementation class
            factory: Optional factory function for complex creation
            lifecycle: Dependency lifecycle (singleton, transient, scoped)
            tags: Optional tags for categorization
            alias: Optional string alias for the registration
            description: Optional description for documentation
        """
        with self._lock:
            if not implementation and not factory:
                raise ValueError(
                    "Either implementation or factory must be provided"
                )
            
            if implementation and interface != implementation:
                # Verify implementation actually implements interface
                if not self._is_implementation_of(implementation, interface):
                    raise TypeError(
                        f"{implementation.__name__} must implement {interface.__name__}"
                    )
            
            metadata = DependencyMetadata(
                tags=tags or [],
                description=description
            )
            
            registration = DependencyRegistration(
                interface=interface,
                implementation=implementation or interface,
                factory=factory,
                lifecycle=lifecycle,
                metadata=metadata
            )
            
            self._registrations[interface] = registration
            
            if alias:
                self._aliases[alias] = interface
            
            self.logger.debug(
                f"Registered {interface.__name__} -> "
                f"{implementation.__name__ if implementation else 'factory'} "
                f"({lifecycle.value})"
            )
            self.metrics.increment("dependencies_registered")
    
    def _is_implementation_of(self, implementation: Type, interface: Type) -> bool:
        """Check if implementation implements interface"""
        # Direct subclass check
        if issubclass(implementation, interface):
            return True
        
        # Duck typing check for protocols
        if hasattr(interface, '__annotations__'):
            interface_attrs = set(dir(interface))
            impl_attrs = set(dir(implementation))
            return interface_attrs.issubset(impl_attrs)
        
        return False
    
    def register_singleton(
        self,
        interface: Type[T],
        implementation: Type[T],
        alias: Optional[str] = None,
        description: Optional[str] = None
    ) -> None:
        """Convenience method for registering singletons"""
        self.register(
            interface,
            implementation,
            lifecycle=Lifecycle.SINGLETON,
            alias=alias,
            description=description
        )
    
    def register_transient(
        self,
        interface: Type[T],
        implementation: Type[T],
        alias: Optional[str] = None,
        description: Optional[str] = None
    ) -> None:
        """Convenience method for registering transients"""
        self.register(
            interface,
            implementation,
            lifecycle=Lifecycle.TRANSIENT,
            alias=alias,
            description=description
        )
    
    def register_scoped(
        self,
        interface: Type[T],
        implementation: Type[T],
        alias: Optional[str] = None,
        description: Optional[str] = None
    ) -> None:
        """Convenience method for registering scoped dependencies"""
        self.register(
            interface,
            implementation,
            lifecycle=Lifecycle.SCOPED,
            alias=alias,
            description=description
        )
    
    def register_instance(
        self,
        interface: Type[T],
        instance: T,
        alias: Optional[str] = None,
        description: Optional[str] = None
    ) -> None:
        """Register an existing instance as a singleton"""
        metadata = DependencyMetadata(description=description)
        
        registration = DependencyRegistration(
            interface=interface,
            implementation=type(instance),
            lifecycle=Lifecycle.SINGLETON,
            metadata=metadata
        )
        registration.instance = instance
        
        self._registrations[interface] = registration
        
        if alias:
            self._aliases[alias] = interface
    
    def register_factory(
        self,
        interface: Type[T],
        factory: Callable[['EnhancedDependencyContainer'], T],
        lifecycle: Lifecycle = Lifecycle.TRANSIENT,
        alias: Optional[str] = None,
        description: Optional[str] = None
    ) -> None:
        """Register a factory function for complex object creation"""
        self.register(
            interface=interface,
            factory=factory,
            lifecycle=lifecycle,
            alias=alias,
            description=description
        )
    
    def resolve(
        self,
        interface: Type[T],
        alias: Optional[str] = None
    ) -> T:
        """
        Resolve a dependency from the container.
        
        Args:
            interface: The interface type to resolve
            alias: Optional alias to resolve instead of interface
            
        Returns:
            Instance of the requested dependency
            
        Raises:
            ValueError: If dependency not registered
            CircularDependencyError: If circular dependency detected
        """
        with self._lock:
            start_time = time.time()
            
            # Resolve alias if provided
            if alias:
                if alias not in self._aliases:
                    raise ValueError(f"No registration found for alias: {alias}")
                interface = self._aliases[alias]
            
            if interface not in self._registrations:
                raise ValueError(
                    f"No registration found for {interface.__name__}"
                )
            
            # Check for circular dependencies
            if interface in self._resolution_stack:
                cycle = [t.__name__ for t in self._resolution_stack] + [interface.__name__]
                raise CircularDependencyError(cycle)
            
            self._resolution_stack.append(interface)
            
            try:
                registration = self._registrations[interface]
                
                with self.tracer.span(
                    f"resolve_{interface.__name__}",
                    tags={
                        "lifecycle": registration.lifecycle.value,
                        "has_factory": registration.factory is not None
                    }
                ):
                    instance = self._create_instance(registration)
                
                # Update statistics
                elapsed_ms = (time.time() - start_time) * 1000
                self._total_resolutions += 1
                self._total_resolution_time_ms += elapsed_ms
                
                self.metrics.increment("dependencies_resolved")
                self.metrics.gauge(
                    "resolution_time_ms",
                    elapsed_ms,
                    tags={"interface": interface.__name__}
                )
                
                return instance
                
            finally:
                self._resolution_stack.pop()
    
    def _create_instance(
        self,
        registration: DependencyRegistration
    ) -> Any:
        """Create instance based on lifecycle"""
        if registration.lifecycle == Lifecycle.SINGLETON:
            if registration.instance is None:
                registration.instance = registration.create_instance(self)
            return registration.instance
            
        elif registration.lifecycle == Lifecycle.TRANSIENT:
            return registration.create_instance(self)
            
        elif registration.lifecycle == Lifecycle.SCOPED:
            if not self._current_scope:
                raise RuntimeError(
                    f"Cannot resolve scoped dependency {registration.interface.__name__} "
                    "outside of a scope. Use 'with container.scope(name):'"
                )
            
            scope = self._scopes[self._current_scope]
            return scope.get_or_create(
                registration.interface.__name__,
                lambda: registration.create_instance(self)
            )
    
    def has_registration(self, interface: Type) -> bool:
        """Check if interface is registered"""
        return interface in self._registrations
    
    def get_registration(
        self,
        interface: Type
    ) -> Optional[DependencyRegistration]:
        """Get registration details for an interface"""
        return self._registrations.get(interface)
    
    def get_registrations_by_tag(self, tag: str) -> List[Type]:
        """Get all registrations with a specific tag"""
        return [
            reg.interface
            for reg in self._registrations.values()
            if tag in reg.metadata.tags
        ]
    
    def get_all_registrations(self) -> Dict[Type, DependencyRegistration]:
        """Get all registrations"""
        return self._registrations.copy()
    
    @contextmanager
    def scope(self, name: str):
        """Create a new dependency scope"""
        with self._lock:
            if name not in self._scopes:
                self._scopes[name] = DependencyScope(name)
            
            previous_scope = self._current_scope
            self._current_scope = name
            
            self.logger.debug(f"Entering scope: {name}")
            self.metrics.increment("scopes_entered")
            
            try:
                yield self._scopes[name]
            finally:
                self._current_scope = previous_scope
                self.logger.debug(f"Exiting scope: {name}")
    
    def clear_scope(self, name: str):
        """Clear all instances in a scope"""
        if name in self._scopes:
            self._scopes[name].clear()
            self.logger.debug(f"Cleared scope: {name}")
    
    def clear_all_scopes(self):
        """Clear all scopes"""
        for scope in self._scopes.values():
            scope.clear()
        self._scopes.clear()
    
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """
        Get the dependency graph for visualization.
        
        Returns:
            Dict mapping interface names to their dependencies
        """
        graph = {}
        
        for interface, registration in self._registrations.items():
            deps = [dep.__name__ for dep in registration.dependencies]
            graph[interface.__name__] = deps
        
        return graph
    
    def validate_registrations(self) -> List[str]:
        """
        Validate all registrations for completeness and circular dependencies.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check for missing dependencies
        for interface, registration in self._registrations.items():
            for dep in registration.dependencies:
                if not self.has_registration(dep):
                    errors.append(
                        f"{interface.__name__} requires {dep.__name__} "
                        f"but it is not registered"
                    )
        
        # Check for circular dependencies using DFS
        graph = self.get_dependency_graph()
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str, path: List[str]) -> Optional[List[str]]:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for dep in graph.get(node, []):
                if dep not in visited:
                    cycle = has_cycle(dep, path.copy())
                    if cycle:
                        return cycle
                elif dep in rec_stack:
                    # Found cycle
                    cycle_start = path.index(dep)
                    return path[cycle_start:] + [dep]
            
            rec_stack.remove(node)
            return None
        
        for node in graph:
            if node not in visited:
                cycle = has_cycle(node, [])
                if cycle:
                    errors.append(
                        f"Circular dependency: {' -> '.join(cycle)}"
                    )
        
        return errors
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive container statistics"""
        stats = {
            "registrations": {
                "total": len(self._registrations),
                "by_lifecycle": {
                    "singleton": sum(
                        1 for r in self._registrations.values()
                        if r.lifecycle == Lifecycle.SINGLETON
                    ),
                    "transient": sum(
                        1 for r in self._registrations.values()
                        if r.lifecycle == Lifecycle.TRANSIENT
                    ),
                    "scoped": sum(
                        1 for r in self._registrations.values()
                        if r.lifecycle == Lifecycle.SCOPED
                    )
                }
            },
            "aliases": len(self._aliases),
            "scopes": {
                "total": len(self._scopes),
                "active": self._current_scope,
                "details": [
                    scope.get_statistics()
                    for scope in self._scopes.values()
                ]
            },
            "performance": {
                "total_resolutions": self._total_resolutions,
                "average_resolution_time_ms": (
                    self._total_resolution_time_ms / self._total_resolutions
                    if self._total_resolutions > 0 else 0
                )
            },
            "top_resolved": self._get_top_resolved(5)
        }
        
        return stats
    
    def _get_top_resolved(self, limit: int) -> List[Dict[str, Any]]:
        """Get most frequently resolved dependencies"""
        sorted_regs = sorted(
            self._registrations.items(),
            key=lambda x: x[1].metadata.resolution_count,
            reverse=True
        )[:limit]
        
        return [
            {
                "interface": interface.__name__,
                "resolution_count": reg.metadata.resolution_count,
                "average_time_ms": reg.metadata.average_resolution_time_ms,
                "lifecycle": reg.lifecycle.value
            }
            for interface, reg in sorted_regs
            if reg.metadata.resolution_count > 0
        ]
    
    def export_registration_summary(self) -> str:
        """Export human-readable registration summary"""
        lines = [
            "Dependency Container Registration Summary",
            "=" * 50,
            ""
        ]
        
        # Group by lifecycle
        by_lifecycle = defaultdict(list)
        for interface, reg in self._registrations.items():
            by_lifecycle[reg.lifecycle].append((interface, reg))
        
        for lifecycle in Lifecycle:
            if lifecycle in by_lifecycle:
                lines.append(f"{lifecycle.value.upper()} Dependencies:")
                lines.append("-" * 30)
                
                for interface, reg in by_lifecycle[lifecycle]:
                    impl_name = (
                        reg.implementation.__name__
                        if reg.implementation else "<factory>"
                    )
                    
                    line = f"  {interface.__name__} -> {impl_name}"
                    
                    if reg.metadata.tags:
                        line += f" [Tags: {', '.join(reg.metadata.tags)}]"
                    
                    if reg.metadata.description:
                        line += f"\n    {reg.metadata.description}"
                    
                    if reg.metadata.resolution_count > 0:
                        line += (
                            f"\n    Resolved: {reg.metadata.resolution_count} times, "
                            f"Avg: {reg.metadata.average_resolution_time_ms:.2f}ms"
                        )
                    
                    lines.append(line)
                
                lines.append("")
        
        # Add statistics
        stats = self.get_statistics()
        lines.extend([
            "Statistics:",
            "-" * 30,
            f"Total Registrations: {stats['registrations']['total']}",
            f"Total Resolutions: {stats['performance']['total_resolutions']}",
            f"Average Resolution Time: {stats['performance']['average_resolution_time_ms']:.2f}ms",
            f"Active Scopes: {len(stats['scopes']['details'])}"
        ])
        
        return "\n".join(lines)