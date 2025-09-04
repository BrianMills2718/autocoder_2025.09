"""
System Generation Module - Emergency Refactoring from system_generator.py

This module contains the refactored components from the massive 3,259-line system_generator.py
organized into focused, maintainable modules under 1,000 lines each.

Modules:
- benchmark_collector: Live industry benchmark collection 
- decision_audit: Decision tracking and transparent analysis
- messaging_analyzer: Evidence-based messaging analysis
- schema_generator: Schema generation logic
- component_generator: Component generation orchestration
- validation_orchestrator: Validation coordination
- deployment_orchestrator: Deployment artifact generation
"""

# Import exceptions and types that are used across modules
from .schema_and_benchmarks import (
    BenchmarkCollectionError,
    SourceValidationError,
    SourceValidationResult,
    LiveBenchmarkData,
    EvidenceBasedAnalysis,
    SystemRequirements,
    LiveIndustryBenchmarkCollector,
)

__all__ = [
    'BenchmarkCollectionError',
    'SourceValidationError', 
    'SourceValidationResult',
    'LiveBenchmarkData',
    'EvidenceBasedAnalysis',
    'SystemRequirements',
]