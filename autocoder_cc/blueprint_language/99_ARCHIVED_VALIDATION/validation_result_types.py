"""
V5.0 Validation Result Types for ValidationDrivenOrchestrator
Central types for four-tier validation hierarchy with fail-hard principles
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from enum import Enum

# Import SemanticValidationResult from semantic_validator
try:
    from .semantic_validator import SemanticValidationResult
except ImportError:
    # Fallback definition if semantic_validator not available
    @dataclass
    class SemanticValidationResult:
        is_reasonable: bool
        reasoning: str
        issues: List[str]
        suggestions: Optional[List[str]] = None


class ValidationLevel(Enum):
    """Four-tier validation hierarchy levels"""
    LEVEL_1_FRAMEWORK = 1
    LEVEL_2_COMPONENT_LOGIC = 2
    LEVEL_3_SYSTEM_INTEGRATION = 3
    LEVEL_4_SEMANTIC_VALIDATION = 4


class FailureType(Enum):
    """Types of validation failures"""
    FRAMEWORK_VALIDATION = "framework_validation"
    COMPONENT_LOGIC_VALIDATION = "component_logic_validation"
    COMPONENT_LOGIC_HEALING_FAILED = "component_logic_healing_failed"
    COMPONENT_LOGIC_ERROR = "component_logic_error"
    SYSTEM_INTEGRATION_VALIDATION = "system_integration_validation"
    SYSTEM_INTEGRATION_HEALING_FAILED = "system_integration_healing_failed"
    SYSTEM_INTEGRATION_ERROR = "system_integration_error"
    SEMANTIC_VALIDATION_FAILURE = "semantic_validation_failure"
    SEMANTIC_HEALING_FAILED = "semantic_healing_failed"
    SEMANTIC_VALIDATION_ERROR = "semantic_validation_error"
    DEPENDENCY_MISSING = "dependency_missing"
    CONFIGURATION_ERROR = "configuration_error"


class HealingType(Enum):
    """Types of healing applied during validation"""
    AST_HEALING = "ast_healing"
    SEMANTIC_HEALING = "semantic_healing"
    CONFIGURATION_REGENERATION = "configuration_regeneration"


@dataclass
class ValidationFailure:
    """Individual validation failure with context and healing information"""
    component_name: Optional[str]
    failure_type: FailureType
    error_message: str
    healing_candidate: bool = False
    severity: str = "ERROR"
    level: Optional[ValidationLevel] = None
    timestamp: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "component_name": self.component_name,
            "failure_type": self.failure_type.value,
            "error_message": self.error_message,
            "healing_candidate": self.healing_candidate,
            "severity": self.severity,
            "level": self.level.value if self.level else None,
            "timestamp": self.timestamp,
            "context": self.context
        }


@dataclass
class HealingResult:
    """Result of healing operation"""
    healing_type: HealingType
    healing_successful: bool
    healed_component: Optional[Any] = None
    healed_blueprint: Optional[Any] = None
    healing_details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "healing_type": self.healing_type.value,
            "healing_successful": self.healing_successful,
            "healing_details": self.healing_details,
            "error_message": self.error_message,
            "execution_time": self.execution_time
        }


@dataclass
class ValidationResult:
    """Result of individual validation level"""
    passed: bool
    level: ValidationLevel
    failures: List[ValidationFailure] = field(default_factory=list)
    healing_applied: bool = False
    healing_results: List[HealingResult] = field(default_factory=list)
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "passed": self.passed,
            "level": self.level.value,
            "failures": [f.to_dict() for f in self.failures],
            "healing_applied": self.healing_applied,
            "healing_results": [h.to_dict() for h in self.healing_results],
            "execution_time": self.execution_time,
            "metadata": self.metadata
        }


@dataclass
class SystemGenerationResult:
    """Complete system generation result from ValidationDrivenOrchestrator"""
    successful: bool
    generated_system: Optional[Any] = None
    validation_levels_passed: int = 0
    validation_results: List[ValidationResult] = field(default_factory=list)
    healing_applied: bool = False
    total_execution_time: float = 0.0
    error_message: Optional[str] = None
    blueprint_path: Optional[str] = None
    timestamp: Optional[str] = None
    
    @property
    def level1_passed(self) -> bool:
        """Check if Level 1 framework validation passed"""
        return any(r.level == ValidationLevel.LEVEL_1_FRAMEWORK and r.passed 
                  for r in self.validation_results)
    
    @property
    def level2_passed(self) -> bool:
        """Check if Level 2 component logic validation passed"""
        return any(r.level == ValidationLevel.LEVEL_2_COMPONENT_LOGIC and r.passed 
                  for r in self.validation_results)
    
    @property
    def level3_passed(self) -> bool:
        """Check if Level 3 system integration validation passed"""
        return any(r.level == ValidationLevel.LEVEL_3_SYSTEM_INTEGRATION and r.passed 
                  for r in self.validation_results)
    
    @property
    def level4_passed(self) -> bool:
        """Check if Level 4 semantic validation passed"""
        return any(r.level == ValidationLevel.LEVEL_4_SEMANTIC_VALIDATION and r.passed 
                  for r in self.validation_results)
    
    @property
    def all_levels_passed(self) -> bool:
        """Check if all four validation levels passed"""
        return (self.level1_passed and self.level2_passed and 
                self.level3_passed and self.level4_passed)
    
    @property
    def system_generated(self) -> bool:
        """Check if system was successfully generated"""
        return self.successful and self.generated_system is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "successful": self.successful,
            "validation_levels_passed": self.validation_levels_passed,
            "validation_results": [r.to_dict() for r in self.validation_results],
            "healing_applied": self.healing_applied,
            "total_execution_time": self.total_execution_time,
            "error_message": self.error_message,
            "blueprint_path": self.blueprint_path,
            "timestamp": self.timestamp,
            "level1_passed": self.level1_passed,
            "level2_passed": self.level2_passed,
            "level3_passed": self.level3_passed,
            "level4_passed": self.level4_passed,
            "all_levels_passed": self.all_levels_passed,
            "system_generated": self.system_generated
        }


# Exception classes for fail-hard validation
class ValidationDependencyError(Exception):
    """Raised when required dependencies are missing - no fallbacks available"""
    pass


class FrameworkValidationError(Exception):
    """Raised when Level 1 framework validation fails"""
    pass


class ComponentLogicValidationError(Exception):
    """Raised when Level 2 component logic validation fails"""
    pass


class SystemIntegrationError(Exception):
    """Raised when Level 3 system integration validation fails"""
    pass


class SemanticValidationError(Exception):
    """Raised when Level 4 semantic validation fails"""
    pass


class ValidationSequenceError(Exception):
    """Raised when validation levels are executed out of sequence"""
    pass


class ComponentSchemaValidationError(Exception):
    """Raised when component fails Phase 2 schema validation"""
    pass


class ComponentGenerationSecurityError(Exception):
    """Raised when generated component fails security validation"""
    pass


class BlueprintValidationError(Exception):
    """Raised when blueprint fails V5.0 validation requirements"""
    pass


class BlueprintParsingError(Exception):
    """Raised when blueprint parsing fails"""
    pass


class LLMUnavailableError(Exception):
    """Raised when LLM is required but not available/responding"""
    pass


# Regeneration result types
@dataclass
class RegenerationStrategy:
    """Strategy for configuration regeneration"""
    requires_port_changes: bool = False
    requires_resource_changes: bool = False
    requires_dependency_changes: bool = False
    changes_applied: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "requires_port_changes": self.requires_port_changes,
            "requires_resource_changes": self.requires_resource_changes,
            "requires_dependency_changes": self.requires_dependency_changes,
            "changes_applied": self.changes_applied
        }


@dataclass
class OrchestratedRegenerationResult:
    """Result of orchestrated configuration regeneration"""
    regeneration_successful: bool
    updated_blueprint: Optional[Any] = None
    regeneration_details: Optional[RegenerationStrategy] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "regeneration_successful": self.regeneration_successful,
            "regeneration_details": self.regeneration_details.to_dict() if self.regeneration_details else None,
            "error_message": self.error_message,
            "execution_time": self.execution_time
        }


@dataclass
class OrchestratedHealingResult:
    """Result of orchestrated healing operation"""
    healing_successful: bool
    healed_component: Optional[Any] = None
    healed_blueprint: Optional[Any] = None
    healing_details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "healing_successful": self.healing_successful,
            "healing_details": self.healing_details,
            "error_message": self.error_message,
            "execution_time": self.execution_time
        }