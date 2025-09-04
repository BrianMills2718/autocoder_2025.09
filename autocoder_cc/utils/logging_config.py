from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
Centralized Logging Configuration for Autocoder V5.2
Provides consistent logging setup across all modules and generated systems
"""

import logging
import sys
from typing import Optional, Dict, Any
from pathlib import Path


class AutocoderLogger:
    """Centralized logging configuration for consistent behavior across Autocoder"""
    
    _initialized: bool = False
    _loggers: Dict[str, logging.Logger] = {}
    
    @classmethod
    def setup_logging(
        cls,
        level: str = "INFO",
        format_string: Optional[str] = None,
        include_timestamp: bool = True,
        include_module: bool = True,
        log_file: Optional[str] = None
    ) -> None:
        """
        Setup centralized logging configuration
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            format_string: Custom format string (optional)
            include_timestamp: Include timestamp in log messages
            include_module: Include module name in log messages  
            log_file: Optional file to write logs to
        """
        if cls._initialized:
            return
            
        # Default format components
        format_parts = []
        if include_timestamp:
            format_parts.append("%(asctime)s")
        if include_module:
            format_parts.append("%(name)s")
        format_parts.extend(["%(levelname)s", "%(message)s"])
        
        # Use custom format or build from components
        if format_string is None:
            format_string = " - ".join(format_parts)
        
        # Configure basic logging
        handlers = [logging.StreamHandler(sys.stdout)]
        if log_file:
            handlers.append(logging.FileHandler(log_file))
            
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format=format_string,
            handlers=handlers,
            force=True  # Override any existing configuration
        )
        
        cls._initialized = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger instance with consistent configuration
        
        Args:
            name: Logger name (typically __name__ or module name)
            
        Returns:
            Configured logger instance
        """
        if not cls._initialized:
            cls.setup_logging()
            
        if name not in cls._loggers:
            cls._loggers[name] = get_logger(name)
            
        return cls._loggers[name]
    
    # Flask logging removed - Enterprise Roadmap v2 forbids Flask
    
    @classmethod
    def setup_generated_system_logging(
        cls,
        system_name: str,
        level: str = "INFO",
        log_directory: Optional[str] = None
    ) -> logging.Logger:
        """
        Setup logging for generated systems with standardized configuration
        
        Args:
            system_name: Name of the generated system
            level: Logging level
            log_directory: Optional directory for log files
            
        Returns:
            Configured logger for the system
        """
        log_file = None
        if log_directory:
            log_path = Path(log_directory)
            log_path.mkdir(exist_ok=True)
            log_file = str(log_path / f"{system_name}.log")
        
        cls.setup_logging(
            level=level,
            log_file=log_file,
            include_timestamp=True,
            include_module=True
        )
        
        return cls.get_logger(system_name)


# Convenience functions for common use cases
def get_logger(name: str = None) -> logging.Logger:
    """Get a logger with standard Autocoder configuration"""
    if name is None:
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'autocoder')
    
    return AutocoderLogger.get_logger(name)


def setup_logging(level: str = "INFO", **kwargs) -> None:
    """Setup logging with standard Autocoder configuration"""
    AutocoderLogger.setup_logging(level=level, **kwargs)


# Flask logging function removed - Enterprise Roadmap v2 forbids Flask


def setup_generated_system_logging(system_name: str, **kwargs) -> logging.Logger:
    """Setup logging for generated systems"""
    return AutocoderLogger.setup_generated_system_logging(system_name, **kwargs)