#!/usr/bin/env python3
"""
Unit Tests for Enhanced Dependency Container

Tests interface-based registration, lifecycle management,
circular dependency detection, and visualization.
"""
import pytest
from typing import Any, Optional
from abc import ABC, abstractmethod
from unittest.mock import Mock, patch
import threading
import time

from autocoder_cc.core.dependency_container import (
    EnhancedDependencyContainer,
    Lifecycle,
    CircularDependencyError,
    DependencyMetadata
)


# Test interfaces and implementations

class IService(ABC):
    """Test service interface"""
    
    @abstractmethod
    def do_work(self) -> str:
        pass


class IRepository(ABC):
    """Test repository interface"""
    
    @abstractmethod
    def get_data(self) -> str:
        pass


class ILogger(ABC):
    """Test logger interface"""
    
    @abstractmethod
    def log(self, message: str) -> None:
        pass


class ServiceImpl(IService):
    """Service implementation with dependencies"""
    
    def __init__(self, repository: IRepository, logger: ILogger):
        self.repository = repository
        self.logger = logger
    
    def do_work(self) -> str:
        data = self.repository.get_data()
        self.logger.log(f"Processing: {data}")
        return f"Processed: {data}"


class RepositoryImpl(IRepository):
    """Repository implementation"""
    
    def __init__(self, logger: ILogger):
        self.logger = logger
    
    def get_data(self) -> str:
        self.logger.log("Getting data")
        return "test_data"


class LoggerImpl(ILogger):
    """Logger implementation"""
    
    def __init__(self):
        self.messages = []
    
    def log(self, message: str) -> None:
        self.messages.append(message)


class CircularServiceA:
    """Service with circular dependency"""
    def __init__(self, service_b: 'CircularServiceB'):
        self.service_b = service_b


class CircularServiceB:
    """Service with circular dependency"""
    def __init__(self, service_a: CircularServiceA):
        self.service_a = service_a


class OptionalDependencyService:
    """Service with optional dependency"""
    def __init__(self, logger: Optional[ILogger] = None):
        self.logger = logger or LoggerImpl()


class TestEnhancedDependencyContainer:
    """Test suite for enhanced dependency container"""
    
    @pytest.fixture
    def container(self):
        """Create a fresh container for each test"""
        with patch('autocoder_cc.core.dependency_container.get_logger') as mock_logger, \
             patch('autocoder_cc.core.dependency_container.get_metrics_collector') as mock_metrics, \
             patch('autocoder_cc.core.dependency_container.get_tracer') as mock_tracer:
            
            mock_logger.return_value = Mock()
            mock_metrics.return_value = Mock()
            mock_tracer.return_value = Mock()
            
            return EnhancedDependencyContainer()
    
    def test_basic_registration_and_resolution(self, container):
        """Test basic dependency registration and resolution"""
        # Register dependencies
        container.register_singleton(ILogger, LoggerImpl)
        container.register_singleton(IRepository, RepositoryImpl)
        container.register_transient(IService, ServiceImpl)
        
        # Resolve service
        service = container.resolve(IService)
        
        assert isinstance(service, ServiceImpl)
        assert isinstance(service.repository, RepositoryImpl)
        assert isinstance(service.logger, LoggerImpl)
        
        # Test functionality
        result = service.do_work()
        assert result == "Processed: test_data"
        assert len(service.logger.messages) == 2
    
    def test_singleton_lifecycle(self, container):
        """Test singleton lifecycle - same instance returned"""
        container.register_singleton(ILogger, LoggerImpl)
        
        logger1 = container.resolve(ILogger)
        logger2 = container.resolve(ILogger)
        
        assert logger1 is logger2
        
        # Verify same instance
        logger1.log("test")
        assert "test" in logger2.messages
    
    def test_transient_lifecycle(self, container):
        """Test transient lifecycle - new instance each time"""
        container.register_transient(ILogger, LoggerImpl)
        
        logger1 = container.resolve(ILogger)
        logger2 = container.resolve(ILogger)
        
        assert logger1 is not logger2
        
        # Verify different instances
        logger1.log("test1")
        logger2.log("test2")
        
        assert "test1" in logger1.messages
        assert "test1" not in logger2.messages
        assert "test2" in logger2.messages
        assert "test2" not in logger1.messages
    
    def test_scoped_lifecycle(self, container):
        """Test scoped lifecycle - same instance within scope"""
        container.register_scoped(ILogger, LoggerImpl)
        
        # Outside scope should fail
        with pytest.raises(RuntimeError, match="outside of a scope"):
            container.resolve(ILogger)
        
        # Within scope
        with container.scope("test_scope") as scope:
            logger1 = container.resolve(ILogger)
            logger2 = container.resolve(ILogger)
            
            assert logger1 is logger2
            
            # Test scope statistics
            stats = scope.get_statistics()
            assert stats["name"] == "test_scope"
            assert stats["instance_count"] == 1
            assert stats["resolution_count"] == 2
        
        # Different scope gets different instance
        with container.scope("another_scope"):
            logger3 = container.resolve(ILogger)
            assert logger3 is not logger1
    
    def test_factory_registration(self, container):
        """Test factory-based registration"""
        def logger_factory(c: EnhancedDependencyContainer) -> ILogger:
            logger = LoggerImpl()
            logger.log("Created by factory")
            return logger
        
        container.register_factory(ILogger, logger_factory)
        
        logger = container.resolve(ILogger)
        assert isinstance(logger, LoggerImpl)
        assert "Created by factory" in logger.messages
    
    def test_instance_registration(self, container):
        """Test registering existing instances"""
        logger_instance = LoggerImpl()
        logger_instance.log("Pre-existing")
        
        container.register_instance(ILogger, logger_instance)
        
        resolved = container.resolve(ILogger)
        assert resolved is logger_instance
        assert "Pre-existing" in resolved.messages
    
    def test_alias_registration(self, container):
        """Test alias-based registration and resolution"""
        container.register_singleton(
            ILogger,
            LoggerImpl,
            alias="main_logger"
        )
        
        # Resolve by interface
        logger1 = container.resolve(ILogger)
        
        # Resolve by alias
        logger2 = container.resolve(ILogger, alias="main_logger")
        
        assert logger1 is logger2
    
    def test_circular_dependency_detection(self, container):
        """Test circular dependency detection"""
        container.register_transient(CircularServiceA, CircularServiceA)
        container.register_transient(CircularServiceB, CircularServiceB)
        
        with pytest.raises(CircularDependencyError) as exc_info:
            container.resolve(CircularServiceA)
        
        assert "Circular dependency detected" in str(exc_info.value)
        assert "CircularServiceA -> CircularServiceB -> CircularServiceA" in str(exc_info.value)
    
    def test_missing_dependency_error(self, container):
        """Test error when dependency is not registered"""
        # Register service but not its dependencies
        container.register_transient(IService, ServiceImpl)
        
        with pytest.raises(ValueError, match="Cannot resolve required dependency"):
            container.resolve(IService)
    
    def test_optional_dependency_handling(self, container):
        """Test handling of optional dependencies"""
        container.register_transient(
            OptionalDependencyService,
            OptionalDependencyService
        )
        
        # Should work without logger registered
        service = container.resolve(OptionalDependencyService)
        assert service.logger is not None
        assert isinstance(service.logger, LoggerImpl)
    
    def test_tag_based_registration(self, container):
        """Test tag-based registration and retrieval"""
        container.register_singleton(
            ILogger,
            LoggerImpl,
            tags=["infrastructure", "logging"]
        )
        
        container.register_singleton(
            IRepository,
            RepositoryImpl,
            tags=["infrastructure", "data"]
        )
        
        # Get by tag
        infra_services = container.get_registrations_by_tag("infrastructure")
        assert len(infra_services) == 2
        assert ILogger in infra_services
        assert IRepository in infra_services
        
        logging_services = container.get_registrations_by_tag("logging")
        assert len(logging_services) == 1
        assert ILogger in logging_services
    
    def test_validation_missing_dependencies(self, container):
        """Test validation detects missing dependencies"""
        # Register service without its dependencies
        container.register_transient(IService, ServiceImpl)
        
        errors = container.validate_registrations()
        assert len(errors) > 0
        assert any("IRepository" in error for error in errors)
        assert any("ILogger" in error for error in errors)
    
    def test_validation_circular_dependencies(self, container):
        """Test validation detects circular dependencies"""
        container.register_transient(CircularServiceA, CircularServiceA)
        container.register_transient(CircularServiceB, CircularServiceB)
        
        errors = container.validate_registrations()
        assert len(errors) > 0
        assert any("Circular dependency" in error for error in errors)
    
    def test_validation_success(self, container):
        """Test validation passes for valid configuration"""
        container.register_singleton(ILogger, LoggerImpl)
        container.register_singleton(IRepository, RepositoryImpl)
        container.register_transient(IService, ServiceImpl)
        
        errors = container.validate_registrations()
        assert len(errors) == 0
    
    def test_dependency_graph_generation(self, container):
        """Test dependency graph generation"""
        container.register_singleton(ILogger, LoggerImpl)
        container.register_singleton(IRepository, RepositoryImpl)
        container.register_transient(IService, ServiceImpl)
        
        graph = container.get_dependency_graph()
        
        assert "ServiceImpl" in graph
        assert "RepositoryImpl" in graph
        assert "LoggerImpl" in graph
        
        # Check dependencies
        assert "IRepository" in graph["ServiceImpl"]
        assert "ILogger" in graph["ServiceImpl"]
        assert "ILogger" in graph["RepositoryImpl"]
        assert len(graph["LoggerImpl"]) == 0
    
    def test_statistics_collection(self, container):
        """Test container statistics collection"""
        container.register_singleton(ILogger, LoggerImpl)
        container.register_transient(IRepository, RepositoryImpl)
        container.register_scoped(IService, ServiceImpl)
        
        # Resolve some dependencies
        logger = container.resolve(ILogger)
        
        with container.scope("test"):
            container.resolve(IRepository)
            container.resolve(IService)
        
        stats = container.get_statistics()
        
        assert stats["registrations"]["total"] == 3
        assert stats["registrations"]["by_lifecycle"]["singleton"] == 1
        assert stats["registrations"]["by_lifecycle"]["transient"] == 1
        assert stats["registrations"]["by_lifecycle"]["scoped"] == 1
        assert stats["performance"]["total_resolutions"] >= 3
    
    def test_performance_tracking(self, container):
        """Test performance metrics tracking"""
        container.register_singleton(ILogger, LoggerImpl)
        
        # Resolve multiple times
        for _ in range(5):
            container.resolve(ILogger)
        
        # Check registration metadata
        registration = container.get_registration(ILogger)
        assert registration.metadata.resolution_count == 5
        assert registration.metadata.average_resolution_time_ms > 0
        assert registration.metadata.last_resolved_at is not None
    
    def test_thread_safety(self, container):
        """Test thread-safe operations"""
        container.register_singleton(ILogger, LoggerImpl)
        
        results = []
        
        def resolve_logger():
            logger = container.resolve(ILogger)
            results.append(logger)
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=resolve_logger)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All should get same singleton instance
        assert len(results) == 10
        assert all(logger is results[0] for logger in results)
    
    def test_export_registration_summary(self, container):
        """Test human-readable summary export"""
        container.register_singleton(
            ILogger,
            LoggerImpl,
            description="Main application logger"
        )
        container.register_transient(
            IRepository,
            RepositoryImpl,
            description="Data repository"
        )
        
        # Resolve to get metrics
        container.resolve(ILogger)
        container.resolve(IRepository)
        
        summary = container.export_registration_summary()
        
        assert "Dependency Container Registration Summary" in summary
        assert "SINGLETON Dependencies:" in summary
        assert "ILogger -> LoggerImpl" in summary
        assert "Main application logger" in summary
        assert "TRANSIENT Dependencies:" in summary
        assert "IRepository -> RepositoryImpl" in summary
        assert "Statistics:" in summary
        assert "Total Registrations: 2" in summary
    
    def test_complex_dependency_chain(self, container):
        """Test resolution of complex dependency chains"""
        # Create a deeper dependency chain
        class IDatabase(ABC):
            @abstractmethod
            def connect(self) -> str:
                pass
        
        class DatabaseImpl(IDatabase):
            def connect(self) -> str:
                return "connected"
        
        class EnhancedRepository(IRepository):
            def __init__(self, database: IDatabase, logger: ILogger):
                self.database = database
                self.logger = logger
            
            def get_data(self) -> str:
                connection = self.database.connect()
                self.logger.log(f"Database {connection}")
                return f"data from {connection}"
        
        # Register all dependencies
        container.register_singleton(ILogger, LoggerImpl)
        container.register_singleton(IDatabase, DatabaseImpl)
        container.register_singleton(IRepository, EnhancedRepository)
        container.register_transient(IService, ServiceImpl)
        
        # Resolve service with deep dependency chain
        service = container.resolve(IService)
        result = service.do_work()
        
        assert "Processed: data from connected" in result
        assert "Database connected" in service.repository.logger.messages
    
    def test_description_and_metadata(self, container):
        """Test description and metadata handling"""
        container.register_singleton(
            ILogger,
            LoggerImpl,
            description="Central logging service",
            tags=["core", "infrastructure"]
        )
        
        registration = container.get_registration(ILogger)
        
        assert registration.metadata.description == "Central logging service"
        assert "core" in registration.metadata.tags
        assert "infrastructure" in registration.metadata.tags
        assert registration.metadata.registered_at is not None