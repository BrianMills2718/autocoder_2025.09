"""
TDD (Test-Driven Development) Framework for AutoCoder

This package provides comprehensive TDD workflow enforcement and automation:
- State tracking to ensure proper TDD phases (RED → GREEN → REFACTOR)
- File operation hooks to prevent violations
- Test runner integration with automatic state updates
- Session management and reporting

Quick Start:
    # Start a new TDD session
    python scripts/tdd_workflow.py start my_feature
    
    # Check current status
    python scripts/tdd_workflow.py status
    
    # Enable TDD enforcement
    from autocoder_cc.tdd import enable_tdd_enforcement
    enable_tdd_enforcement()
"""

from .state_tracker import (
    TDDStateTracker,
    TDDPhase,
    TDDViolation,
    TDDSession,
    TestResult,
    get_tracker,
)

from .file_hooks import (
    TDDFileHooks,
    enable_tdd_enforcement,
    disable_tdd_enforcement,
    get_hooks,
    tdd_validated_write,
    tdd_validated_create,
)

from .test_runner import (
    TDDTestRunner,
    run_tdd_tests,
    watch_tdd_tests,
)

__all__ = [
    # State tracking
    'TDDStateTracker',
    'TDDPhase',
    'TDDViolation',
    'TDDSession',
    'TestResult',
    'get_tracker',
    
    # File hooks
    'TDDFileHooks',
    'enable_tdd_enforcement',
    'disable_tdd_enforcement',
    'get_hooks',
    'tdd_validated_write',
    'tdd_validated_create',
    
    # Test runner
    'TDDTestRunner',
    'run_tdd_tests',
    'watch_tdd_tests',
]