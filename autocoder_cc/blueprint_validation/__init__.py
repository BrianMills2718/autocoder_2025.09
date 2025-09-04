"""
VR1 Blueprint Validation Package

Implements VR1 boundary-termination validation with port-faithful path traversal
"""

from .vr1_validator import VR1Validator, TerminationMode, PathTraversalState, ReachabilityResult
from .boundary_semantics import BoundarySemantics, CommitmentType, CommitmentPredicate
from .vr1_error_taxonomy import (
    VR1ErrorType, VR1ErrorCategory, VR1ValidationError, VR1ErrorContext, VR1ErrorFactory
)
from .vr1_telemetry import VR1TelemetryCollector, VR1TelemetryContext, vr1_telemetry
from .migration_engine import (
    BlueprintMigrationEngine, AutoHealingEngine, MigrationType, MigrationOperation, MigrationResult
)
from .vr1_rollout import VR1RolloutManager, VR1ValidationCoordinator, vr1_coordinator

__all__ = [
    'VR1Validator',
    'TerminationMode', 
    'PathTraversalState',
    'ReachabilityResult',
    'BoundarySemantics',
    'CommitmentType',
    'CommitmentPredicate',
    'VR1ErrorType',
    'VR1ErrorCategory', 
    'VR1ValidationError',
    'VR1ErrorContext',
    'VR1ErrorFactory',
    'VR1TelemetryCollector',
    'VR1TelemetryContext',
    'vr1_telemetry',
    'BlueprintMigrationEngine',
    'AutoHealingEngine',
    'MigrationType',
    'MigrationOperation',
    'MigrationResult',
    'VR1RolloutManager',
    'VR1ValidationCoordinator',
    'vr1_coordinator'
]