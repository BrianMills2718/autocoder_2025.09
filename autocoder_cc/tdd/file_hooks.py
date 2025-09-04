#!/usr/bin/env python3
"""
TDD File Operation Hooks - Enforces TDD workflow during file operations
"""
import os
from pathlib import Path
from typing import Optional, Callable
from functools import wraps

from .state_tracker import TDDStateTracker, TDDPhase, TDDViolation


class TDDFileHooks:
    """Hooks for enforcing TDD during file operations"""
    
    def __init__(self, tracker: Optional[TDDStateTracker] = None):
        """Initialize with optional tracker instance"""
        self.tracker = tracker or TDDStateTracker()
        self._enabled = os.getenv('TDD_ENFORCEMENT', 'false').lower() == 'true'
    
    def enable(self):
        """Enable TDD enforcement"""
        self._enabled = True
        os.environ['TDD_ENFORCEMENT'] = 'true'
    
    def disable(self):
        """Disable TDD enforcement"""
        self._enabled = False
        os.environ['TDD_ENFORCEMENT'] = 'false'
    
    def validate_write(self, file_path: str, content: str) -> None:
        """Validate write operation against TDD rules"""
        if not self._enabled:
            return
        
        try:
            self.tracker.validate_file_operation(file_path, 'WRITE')
        except TDDViolation as e:
            # Check if user wants to override
            if os.getenv('TDD_OVERRIDE', 'false').lower() == 'true':
                print(f"⚠️ TDD Override: {e}")
                return
            raise
    
    def validate_create(self, file_path: str) -> None:
        """Validate file creation against TDD rules"""
        if not self._enabled:
            return
        
        try:
            self.tracker.validate_file_operation(file_path, 'CREATE')
        except TDDViolation as e:
            # Check if user wants to override
            if os.getenv('TDD_OVERRIDE', 'false').lower() == 'true':
                print(f"⚠️ TDD Override: {e}")
                return
            raise
    
    def wrap_file_operation(self, operation: str):
        """Decorator for wrapping file operations with TDD validation"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(file_path: str, *args, **kwargs):
                # Validate operation
                if self._enabled and operation in ['WRITE', 'CREATE']:
                    try:
                        self.tracker.validate_file_operation(file_path, operation)
                    except TDDViolation as e:
                        if os.getenv('TDD_OVERRIDE', 'false').lower() != 'true':
                            raise
                        print(f"⚠️ TDD Override: {e}")
                
                # Execute operation
                return func(file_path, *args, **kwargs)
            return wrapper
        return decorator
    
    def suggest_action(self, file_path: str) -> str:
        """Suggest appropriate action based on current TDD state"""
        if not self.tracker.current_session:
            return "Start a TDD session first: tdd_workflow.py start <feature_name>"
        
        path = Path(file_path)
        is_test = 'test' in path.name.lower() or 'tests' in path.parts
        phase = self.tracker.get_current_phase()
        
        if phase == TDDPhase.RED and not is_test:
            return "Write failing tests first before implementing"
        elif phase == TDDPhase.GREEN and is_test:
            return "Writing new tests will transition back to RED phase"
        elif phase == TDDPhase.REFACTOR:
            return "Refactor code while keeping tests green"
        
        return self.tracker.suggest_next_action()


# Global hooks instance
_hooks = TDDFileHooks()


def enable_tdd_enforcement():
    """Enable TDD enforcement globally"""
    _hooks.enable()
    print("✅ TDD enforcement enabled")


def disable_tdd_enforcement():
    """Disable TDD enforcement globally"""
    _hooks.disable()
    print("❌ TDD enforcement disabled")


def get_hooks() -> TDDFileHooks:
    """Get global TDD file hooks instance"""
    return _hooks


# Decorators for use with file operations
def tdd_validated_write(func: Callable) -> Callable:
    """Decorator to add TDD validation to write operations"""
    return _hooks.wrap_file_operation('WRITE')(func)


def tdd_validated_create(func: Callable) -> Callable:
    """Decorator to add TDD validation to file creation"""
    return _hooks.wrap_file_operation('CREATE')(func)