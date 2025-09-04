#!/usr/bin/env python3
"""
Dependency Injection Container for AutoCoder4_CC
Resolves circular import issues and provides clean dependency management.
"""

from typing import Dict, Type, TypeVar, Callable, Any, Protocol, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import threading
import weakref
from autocoder_cc.observability.structured_logging import get_logger

T = TypeVar('T')
ServiceType = TypeVar('ServiceType')

class ServiceProtocol(Protocol):
    """Base protocol for all injectable services"""
    pass

@dataclass
class ServiceRegistration:
    """Service registration configuration"""
    service_type: Type
    factory: Callable[[], Any]
    singleton: bool = False
    lazy: bool = True
    dependencies: Optional[list] = None

class DependencyInjectionContainer:
    """
    Central dependency injection container that resolves circular imports
    and manages component lifecycle.
    
    Features:
    - Lazy loading to avoid circular imports
    - Singleton and transient service lifetimes
    - Protocol-based interface registration
    - Thread-safe service resolution
    """
    
    def __init__(self):
        self._services: Dict[Type, ServiceRegistration] = {}
        self._instances: Dict[Type, weakref.ref] = {}
        self._singletons: Dict[Type, Any] = {}
        self._lock = threading.RLock()
        self.logger = get_logger(__name__)
        
        self.logger.info("🔧 Dependency Injection Container initialized")
    
    def register_factory(self, 
                        interface: Type[T], 
                        factory: Callable[[], T], 
                        singleton: bool = False,
                        dependencies: Optional[list] = None) -> None:
        """
        Register a factory function for lazy service instantiation.
        
        Args:
            interface: Service interface/type to register
            factory: Factory function that creates the service
            singleton: Whether to create only one instance
            dependencies: List of dependency types this service needs
        """
        with self._lock:
            registration = ServiceRegistration(
                service_type=interface,
                factory=factory,
                singleton=singleton,
                lazy=True,
                dependencies=dependencies or []
            )
            self._services[interface] = registration
            self.logger.debug(f"📝 Registered factory for {interface.__name__}")
    
    def register_singleton(self, interface: Type[T], instance: T) -> None:
        """
        Register a singleton instance directly.
        
        Args:
            interface: Service interface/type
            instance: Pre-created instance to register
        """
        with self._lock:
            self._singletons[interface] = instance
            self.logger.debug(f"📝 Registered singleton for {interface.__name__}")
    
    def register_transient(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """
        Register a transient service (new instance each time).
        
        Args:
            interface: Service interface/type
            factory: Factory function that creates new instances
        """
        self.register_factory(interface, factory, singleton=False)
    
    def get(self, interface: Type[T]) -> T:
        """
        Get or create a service instance.
        
        Args:
            interface: Service interface/type to retrieve
            
        Returns:
            Service instance
            
        Raises:
            ValueError: If no factory is registered for the interface
        """
        with self._lock:
            # Check if already a singleton instance
            if interface in self._singletons:
                return self._singletons[interface]
            
            # Check if we have a registration
            if interface not in self._services:
                raise ValueError(f"No factory registered for {interface.__name__}")
            
            registration = self._services[interface]
            
            # For singletons, check if we already created an instance
            if registration.singleton and interface in self._instances:
                instance = self._instances[interface]()
                if instance is not None:
                    return instance
            
            # Create new instance
            try:
                self.logger.debug(f"🏭 Creating instance of {interface.__name__}")
                instance = registration.factory()
                
                # Store singleton instances
                if registration.singleton:
                    self._instances[interface] = weakref.ref(instance)
                    
                return instance
                
            except Exception as e:
                self.logger.error(f"❌ Failed to create {interface.__name__}: {e}")
                raise ValueError(f"Failed to create instance of {interface.__name__}: {e}")
    
    def get_optional(self, interface: Type[T]) -> Optional[T]:
        """
        Get a service instance if registered, otherwise return None.
        
        Args:
            interface: Service interface/type to retrieve
            
        Returns:
            Service instance or None if not registered
        """
        try:
            return self.get(interface)
        except ValueError:
            return None
    
    def clear(self) -> None:
        """Clear all registrations and instances (for testing)"""
        with self._lock:
            self._services.clear()
            self._instances.clear()
            self._singletons.clear()
            self.logger.debug("🧹 Cleared all service registrations")
    
    def is_registered(self, interface: Type) -> bool:
        """Check if a service is registered"""
        return interface in self._services or interface in self._singletons
    
    def list_registrations(self) -> Dict[str, Dict[str, Any]]:
        """Get a list of all registered services (for debugging)"""
        registrations = {}
        for interface, registration in self._services.items():
            registrations[interface.__name__] = {
                'singleton': registration.singleton,
                'lazy': registration.lazy,
                'dependencies': [dep.__name__ for dep in registration.dependencies] if registration.dependencies else []
            }
        for interface in self._singletons:
            registrations[interface.__name__] = {
                'singleton': True,
                'lazy': False,
                'type': 'direct_instance'
            }
        return registrations

# Global container instance
_container: Optional[DependencyInjectionContainer] = None
_container_lock = threading.Lock()

def get_container() -> DependencyInjectionContainer:
    """Get the global dependency injection container (singleton)"""
    global _container
    if _container is None:
        with _container_lock:
            if _container is None:
                _container = DependencyInjectionContainer()
    return _container

def inject(interface: Type[T]) -> T:
    """
    Decorator/function to inject dependencies.
    
    Usage:
        # As a function
        component_generator = inject(ComponentGeneratorProtocol)
        
        # In a method
        def some_method(self):
            generator = inject(ComponentGeneratorProtocol)
            return generator.generate_component(...)
    """
    return get_container().get(interface)

def register_service(interface: Type[T], 
                    factory: Callable[[], T], 
                    singleton: bool = False) -> None:
    """
    Convenience function to register a service.
    
    Args:
        interface: Service interface/type
        factory: Factory function
        singleton: Whether to create only one instance
    """
    get_container().register_factory(interface, factory, singleton)

def register_singleton_instance(interface: Type[T], instance: T) -> None:
    """
    Convenience function to register a singleton instance.
    
    Args:
        interface: Service interface/type
        instance: Pre-created instance
    """
    get_container().register_singleton(interface, instance)

# Decorator for auto-registration
def injectable(interface: Type[T], singleton: bool = False):
    """
    Class decorator to automatically register a class as a service.
    
    Usage:
        @injectable(ComponentGeneratorProtocol, singleton=True)
        class MyComponentGenerator:
            def generate_component(self, ...):
                ...
    """
    def decorator(cls):
        def factory():
            return cls()
        register_service(interface, factory, singleton)
        return cls
    return decorator