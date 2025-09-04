#!/usr/bin/env python3
"""
Process Executor Abstraction for Autocoder V5.2

Provides an abstraction layer for subprocess interactions to enable
dependency injection and comprehensive testing.
"""

import subprocess
import asyncio
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ProcessResult:
    """Result of a process execution."""
    returncode: int
    stdout: str
    stderr: str
    execution_time: float


class ProcessExecutor(ABC):
    """Abstract base class for process execution."""
    
    @abstractmethod
    async def run(
        self,
        command: List[str],
        input_data: Optional[str] = None,
        timeout: Optional[float] = None,
        capture_output: bool = True,
        text: bool = True,
        **kwargs
    ) -> ProcessResult:
        """Execute a process with the given command and parameters."""
        pass


class SubprocessExecutor(ProcessExecutor):
    """Concrete implementation using subprocess module."""
    
    async def run(
        self,
        command: List[str],
        input_data: Optional[str] = None,
        timeout: Optional[float] = None,
        capture_output: bool = True,
        text: bool = True,
        **kwargs
    ) -> ProcessResult:
        """Execute a process using subprocess."""
        import time
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                input=input_data,
                capture_output=capture_output,
                text=text,
                timeout=timeout,
                **kwargs
            )
            
            execution_time = time.time() - start_time
            
            return ProcessResult(
                returncode=result.returncode,
                stdout=result.stdout if result.stdout else "",
                stderr=result.stderr if result.stderr else "",
                execution_time=execution_time
            )
            
        except subprocess.TimeoutExpired as e:
            execution_time = time.time() - start_time
            raise TimeoutError(f"Process timed out after {execution_time:.2f}s") from e
        except FileNotFoundError as e:
            execution_time = time.time() - start_time
            raise FileNotFoundError(f"Command not found: {command[0]}") from e


class MockProcessExecutor(ProcessExecutor):
    """Mock implementation for testing."""
    
    def __init__(self):
        self.executed_commands: List[Dict[str, Any]] = []
        self.mock_responses: Dict[str, ProcessResult] = {}
        self.default_response = ProcessResult(
            returncode=0,
            stdout="mock output",
            stderr="",
            execution_time=0.1
        )
    
    def set_mock_response(self, command_pattern: str, response: ProcessResult):
        """Set a mock response for a command pattern."""
        self.mock_responses[command_pattern] = response
    
    async def run(
        self,
        command: List[str],
        input_data: Optional[str] = None,
        timeout: Optional[float] = None,
        capture_output: bool = True,
        text: bool = True,
        **kwargs
    ) -> ProcessResult:
        """Mock process execution for testing."""
        # Record the executed command
        self.executed_commands.append({
            "command": command,
            "input_data": input_data,
            "timeout": timeout,
            "capture_output": capture_output,
            "text": text,
            "kwargs": kwargs
        })
        
        # Find matching mock response
        command_str = " ".join(command)
        for pattern, response in self.mock_responses.items():
            if pattern in command_str:
                return response
        
        # Return default response if no specific mock found
        return self.default_response