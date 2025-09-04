"""
VR1 Staged Rollout System

Manages feature flags, environment-based rollout, and graceful fallback to legacy validation
for safe deployment of VR1 boundary-termination validation.
"""

import os
import logging
from typing import Tuple, List, Optional
from copy import deepcopy

from ..blueprint_language.blueprint_parser import ParsedBlueprint
from .migration_engine import BlueprintMigrationEngine, AutoHealingEngine
from .vr1_error_taxonomy import VR1ValidationError


class VR1RolloutManager:
    """
    Staged rollout manager for VR1 boundary-termination validation
    
    Manages feature flags, environment-based rollout, and graceful fallback to legacy validation
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def should_use_vr1_validation(self, blueprint: ParsedBlueprint, 
                                environment: str = "development") -> bool:
        """
        Determine whether to use VR1 validation based on rollout configuration
        """
        
        # Check global feature flag
        if not self._is_vr1_globally_enabled():
            return False
        
        # Check environment-specific rollout
        if not self._is_vr1_enabled_for_environment(environment):
            return False
        
        # Check blueprint version
        blueprint_version = getattr(blueprint, 'version', '1.0.0')
        if not self._is_blueprint_version_eligible(blueprint_version):
            return False
        
        # Check component count (gradual rollout by complexity)
        component_count = 1  # Single component blueprints for now
        if not self._is_component_count_eligible(component_count, environment):
            return False
        
        return True
    
    def _is_vr1_globally_enabled(self) -> bool:
        """Check global VR1 feature flag"""
        return os.getenv("BOUNDARY_TERMINATION_ENABLED", "false").lower() == "true"
    
    def _is_vr1_enabled_for_environment(self, environment: str) -> bool:
        """Check environment-specific VR1 rollout"""
        rollout_environments = os.getenv("VR1_ROLLOUT_ENVIRONMENTS", "development").split(",")
        return environment.lower() in [env.strip().lower() for env in rollout_environments]
    
    def _is_blueprint_version_eligible(self, version: str) -> bool:
        """Check if blueprint version is eligible for VR1"""
        try:
            from packaging import version as pkg_version
            parsed_version = pkg_version.parse(version)
            min_version = pkg_version.parse("1.1.0")
            return parsed_version >= min_version
        except Exception:
            # Default to eligible if version parsing fails
            return True
    
    def _is_component_count_eligible(self, component_count: int, environment: str) -> bool:
        """Gradual rollout based on blueprint complexity"""
        
        if environment == "development":
            return True  # All blueprints eligible in development
        
        elif environment == "staging":
            max_components = int(os.getenv("VR1_STAGING_MAX_COMPONENTS", "20"))
            return component_count <= max_components
        
        elif environment == "production":
            max_components = int(os.getenv("VR1_PRODUCTION_MAX_COMPONENTS", "10"))
            return component_count <= max_components
        
        return False


class VR1ValidationCoordinator:
    """
    Coordination layer that manages migration, auto-healing, and staged rollout
    """
    
    def __init__(self):
        self.migration_engine = BlueprintMigrationEngine()
        self.auto_healing = AutoHealingEngine(self.migration_engine)
        self.rollout_manager = VR1RolloutManager()
        self.logger = logging.getLogger(__name__)
    
    def validate_with_vr1_coordination(self, blueprint: ParsedBlueprint,
                                     environment: str = "development",
                                     force_vr1: bool = False) -> Tuple[bool, List[str], Optional[ParsedBlueprint]]:
        """
        Coordinate VR1 validation with migration, auto-healing, and rollout management
        
        Returns:
            (validation_success, actions_taken, final_blueprint)
        """
        actions_taken = []
        
        # Phase 1: Check rollout eligibility
        should_use_vr1 = force_vr1 or self.rollout_manager.should_use_vr1_validation(blueprint, environment)
        
        if not should_use_vr1:
            actions_taken.append("Using legacy validation (VR1 not enabled for this context)")
            # Fall back to legacy validation
            return self._use_legacy_validation(blueprint, actions_taken)
        
        # Phase 2: Auto-migration
        migration_result = self.migration_engine.migrate_blueprint(blueprint)
        
        if migration_result.migration_needed:
            if migration_result.migrated_blueprint:
                blueprint = migration_result.migrated_blueprint
                actions_taken.append(f"Auto-migrated blueprint: {migration_result.migration_type.value}")
                actions_taken.extend([f"  - {op.justification}" for op in migration_result.operations_applied])
            else:
                actions_taken.append(f"Migration failed: {migration_result.warnings}")
                return False, actions_taken, blueprint
        
        # Phase 3: VR1 validation attempt
        validation_result, vr1_errors = self._perform_vr1_validation(blueprint)
        
        if validation_result:
            actions_taken.append("VR1 validation passed")
            return True, actions_taken, blueprint
        
        # Phase 4: Auto-healing attempt
        if vr1_errors:
            healed_blueprint, healing_actions = self.auto_healing.auto_heal_validation_failures(
                blueprint, vr1_errors
            )
            
            if healing_actions:
                actions_taken.extend([f"Auto-healing: {action}" for action in healing_actions])
                
                # Retry validation with healed blueprint
                retry_result, _ = self._perform_vr1_validation(healed_blueprint)
                
                if retry_result:
                    actions_taken.append("VR1 validation passed after auto-healing")
                    return True, actions_taken, healed_blueprint
        
        # Phase 5: VR1 validation failed - log and potentially fall back
        actions_taken.append("VR1 validation failed")
        if environment == "production":
            actions_taken.append("Falling back to legacy validation in production")
            return self._use_legacy_validation(blueprint, actions_taken)
        
        return False, actions_taken, blueprint
    
    def _perform_vr1_validation(self, blueprint: ParsedBlueprint) -> Tuple[bool, List[VR1ValidationError]]:
        """Perform VR1 validation and extract structured errors"""
        try:
            from .vr1_validator import VR1Validator
            vr1_validator = VR1Validator(blueprint)
            validation_result = vr1_validator.validate_boundary_termination()
            
            # Extract VR1 errors if available
            vr1_errors = []
            if not validation_result.passed and hasattr(validation_result, 'metadata'):
                # Try to extract VR1 errors from reachability results
                reachability_results = validation_result.metadata.get('reachability_results', [])
                for result in reachability_results:
                    if not result.termination_found:
                        # Create VR1 error from failed reachability
                        from .vr1_error_taxonomy import VR1ErrorFactory
                        error = VR1ErrorFactory.reply_commitment_unmet(
                            blueprint.component.name, 
                            "request",  # Default port name
                            result.path_trace
                        )
                        vr1_errors.append(error)
            
            return validation_result.passed, vr1_errors
            
        except Exception as e:
            self.logger.exception("VR1 validation failed with exception")
            return False, []
    
    def _use_legacy_validation(self, blueprint: ParsedBlueprint, 
                             actions_taken: List[str]) -> Tuple[bool, List[str], ParsedBlueprint]:
        """Fall back to legacy validation"""
        try:
            # For now, we'll implement a simple legacy validator that always passes
            # In a real system, this would use the existing validation logic
            legacy_result = self._simple_legacy_validation(blueprint)
            
            if legacy_result:
                actions_taken.append("Legacy validation passed")
                return True, actions_taken, blueprint
            else:
                actions_taken.append("Legacy validation failed")
                return False, actions_taken, blueprint
                
        except Exception as e:
            self.logger.exception("Legacy validation failed")
            actions_taken.append(f"Legacy validation error: {str(e)}")
            return False, actions_taken, blueprint
    
    def _simple_legacy_validation(self, blueprint: ParsedBlueprint) -> bool:
        """Simple legacy validation for fallback"""
        try:
            # Basic structural validation
            component = blueprint.component
            
            # Must have a name and type
            if not component.name or not component.type:
                return False
            
            # Must have at least inputs or outputs
            if not component.inputs and not component.outputs:
                return False
            
            # Valid component types
            valid_types = [
                "APIEndpoint", "WebSocket", "Store", "Controller", "Transformer",
                "Source", "Sink", "StreamProcessor", "Model", "Accumulator",
                "Router", "Aggregator", "Filter"
            ]
            
            if component.type not in valid_types:
                return False
            
            return True
            
        except Exception:
            return False


# Global coordinator instance for easy access
vr1_coordinator = VR1ValidationCoordinator()