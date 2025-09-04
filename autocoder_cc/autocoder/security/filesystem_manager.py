#!/usr/bin/env python3
"""
FileSystem Manager Abstraction for Autocoder V5.2

Provides an abstraction layer for file system operations to enable
dependency injection and comprehensive testing.
"""

import tempfile
import os
from typing import Optional, Any
from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path


class FileSystemManager(ABC):
    """Abstract base class for file system operations."""
    
    @abstractmethod
    @contextmanager
    def temporary_file(
        self,
        mode: str = 'w',
        suffix: Optional[str] = None,
        prefix: Optional[str] = None,
        delete: bool = True,
        **kwargs
    ):
        """Create a temporary file context manager."""
        pass
    
    @abstractmethod
    def remove_file(self, file_path: str) -> None:
        """Remove a file from the filesystem."""
        pass


class TempFileManager(FileSystemManager):
    """Concrete implementation using tempfile module."""
    
    @contextmanager
    def temporary_file(
        self,
        mode: str = 'w',
        suffix: Optional[str] = None,
        prefix: Optional[str] = None,
        delete: bool = True,
        **kwargs
    ):
        """Create a temporary file using tempfile."""
        temp_file = tempfile.NamedTemporaryFile(
            mode=mode,
            suffix=suffix,
            prefix=prefix,
            delete=delete,
            **kwargs
        )
        
        try:
            yield temp_file
        finally:
            if not delete and hasattr(temp_file, 'name') and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except OSError:
                    pass
    
    def remove_file(self, file_path: str) -> None:
        """Remove a file using os.unlink."""
        try:
            os.unlink(file_path)
        except OSError:
            pass


class MockFileSystemManager(FileSystemManager):
    """Mock implementation for testing."""
    
    def __init__(self):
        self.created_files: list = []
        self.removed_files: list = []
        self.file_contents: dict = {}
        self._temp_file_counter = 0
    
    @contextmanager
    def temporary_file(
        self,
        mode: str = 'w',
        suffix: Optional[str] = None,
        prefix: Optional[str] = None,
        delete: bool = True,
        **kwargs
    ):
        """Mock temporary file creation."""
        self._temp_file_counter += 1
        mock_filename = f"/tmp/mock_temp_file_{self._temp_file_counter}{suffix or ''}"
        
        # Create a mock file object
        class MockTempFile:
            def __init__(self, name: str):
                self.name = name
                self.content = ""
                self.closed = False
            
            def write(self, content: str):
                self.content += content
            
            def flush(self):
                pass
            
            def close(self):
                self.closed = True
        
        mock_file = MockTempFile(mock_filename)
        self.created_files.append(mock_filename)
        
        try:
            yield mock_file
            # Store the content for inspection
            self.file_contents[mock_filename] = mock_file.content
        finally:
            mock_file.close()
            if not delete:
                # Simulate cleanup
                self.remove_file(mock_filename)
    
    def remove_file(self, file_path: str) -> None:
        """Mock file removal."""
        self.removed_files.append(file_path)
        if file_path in self.file_contents:
            del self.file_contents[file_path]