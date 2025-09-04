"""
Research Validation Framework - Task 17 Implementation

Comprehensive citation verification and research data validation
for ensuring all industry standards and benchmarks are accurate.
"""

from .citation_validator import (
    CitationValidator,
    CitationSource,
    CitationValidation,
    ResearchDataValidation,
    ValidationReport as CitationValidationReport
)

from .research_validator import (
    ResearchValidator,
    BenchmarkClaim,
    ThresholdDecision,
    StatisticalValidation,
    CorrelationAnalysis,
    ValidationReport as ResearchValidationReport
)

__all__ = [
    # Citation Validation
    'CitationValidator',
    'CitationSource', 
    'CitationValidation',
    'ResearchDataValidation',
    'CitationValidationReport',
    
    # Research Data Validation
    'ResearchValidator',
    'BenchmarkClaim',
    'ThresholdDecision',
    'StatisticalValidation',
    'CorrelationAnalysis',
    'ResearchValidationReport'
]

# Package version
__version__ = "1.0.0"

# Package description
__description__ = "Research validation framework for citation verification and data validation"