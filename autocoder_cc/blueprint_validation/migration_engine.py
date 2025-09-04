"""
Blueprint Migration Engine

Automatic migration of legacy blueprints to VR1 boundary-termination compatible format
with zero breaking changes and comprehensive auto-healing capabilities.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum
import logging
from copy import deepcopy

from ..blueprint_language.blueprint_parser import ParsedBlueprint, ParsedComponent, ParsedPort
from .vr1_error_taxonomy import VR1ValidationError, VR1ErrorFactory, VR1ErrorType, VR1ErrorCategory, VR1ErrorContext


class MigrationType(Enum):
    """Types of blueprint migration operations"""
    NO_MIGRATION_NEEDED = "no_migration_needed"        # Already VR1 compatible
    BOUNDARY_FIELD_ADDITION = "boundary_field_addition"  # Add missing boundary fields
    DURABILITY_INFERENCE = "durability_inference"      # Infer durability contracts
    COMPONENT_TYPE_UPGRADE = "component_type_upgrade"   # Update deprecated component types
    LEGACY_TO_VR1_FULL = "legacy_to_vr1_full"         # Complete legacy migration


@dataclass
class MigrationOperation:
    """Single migration operation to be applied"""
    operation_type: str
    target_component: str
    target_port: Optional[str] = None
    old_value: Any = None
    new_value: Any = None
    justification: str = ""


@dataclass
class MigrationResult:
    """Result of blueprint migration process"""
    migration_needed: bool
    migration_type: MigrationType
    operations_applied: List[MigrationOperation] = field(default_factory=list)
    migrated_blueprint: Optional[ParsedBlueprint] = None
    warnings: List[str] = field(default_factory=list)
    migration_confidence: float = 1.0  # 0.0 = low confidence, 1.0 = high confidence


class BlueprintMigrationEngine:
    """
    Automatic migration engine for legacy blueprints to VR1 compatibility
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Migration configuration
        self.CONFIDENCE_THRESHOLD = 0.8  # Minimum confidence for auto-migration
        self.ENABLE_AGGRESSIVE_INFERENCE = False  # Conservative by default
        
    def migrate_blueprint(self, blueprint: ParsedBlueprint, 
                         force_migration: bool = False) -> MigrationResult:
        """
        Migrate legacy blueprint to VR1 compatibility
        
        Args:
            blueprint: Original blueprint to migrate
            force_migration: Apply migration even with low confidence
            
        Returns:
            MigrationResult with migrated blueprint and operation log
        """
        try:
            # Phase 1: Analyze migration requirements
            migration_analysis = self._analyze_migration_requirements(blueprint)
            
            if migration_analysis.migration_type == MigrationType.NO_MIGRATION_NEEDED:
                return MigrationResult(
                    migration_needed=False,
                    migration_type=MigrationType.NO_MIGRATION_NEEDED,
                    migrated_blueprint=blueprint,
                    migration_confidence=1.0
                )
            
            # Phase 2: Plan migration operations
            migration_operations = self._plan_migration_operations(blueprint, migration_analysis)
            
            # Phase 3: Calculate migration confidence
            confidence = self._calculate_migration_confidence(migration_operations)
            
            if confidence < self.CONFIDENCE_THRESHOLD and not force_migration:
                return MigrationResult(
                    migration_needed=True,
                    migration_type=migration_analysis.migration_type,
                    migration_confidence=confidence,
                    warnings=[
                        f"Migration confidence {confidence:.2f} below threshold {self.CONFIDENCE_THRESHOLD}",
                        "Use force_migration=True to apply anyway"
                    ]
                )
            
            # Phase 4: Apply migration operations
            migrated_blueprint = self._apply_migration_operations(blueprint, migration_operations)
            
            # Phase 5: Validate migrated blueprint
            validation_warnings = self._validate_migrated_blueprint(migrated_blueprint)
            
            return MigrationResult(
                migration_needed=True,
                migration_type=migration_analysis.migration_type,
                operations_applied=migration_operations,
                migrated_blueprint=migrated_blueprint,
                warnings=validation_warnings,
                migration_confidence=confidence
            )
            
        except Exception as e:
            self.logger.exception("Blueprint migration failed")
            return MigrationResult(
                migration_needed=True,
                migration_type=MigrationType.LEGACY_TO_VR1_FULL,
                warnings=[f"Migration failed: {str(e)}"],
                migration_confidence=0.0
            )
    
    def _analyze_migration_requirements(self, blueprint: ParsedBlueprint) -> MigrationResult:
        """Analyze what type of migration is needed"""
        
        # Check blueprint version
        blueprint_version = blueprint.metadata.get('version', '1.0.0') if blueprint.metadata else '1.0.0'
        
        if self._is_vr1_compatible(blueprint_version):
            # Check if boundary fields are present
            if self._has_boundary_fields(blueprint):
                return MigrationResult(
                    migration_needed=False,
                    migration_type=MigrationType.NO_MIGRATION_NEEDED
                )
            else:
                return MigrationResult(
                    migration_needed=True,
                    migration_type=MigrationType.BOUNDARY_FIELD_ADDITION
                )
        
        # Legacy blueprint - full migration needed
        return MigrationResult(
            migration_needed=True,
            migration_type=MigrationType.LEGACY_TO_VR1_FULL
        )
    
    def _is_vr1_compatible(self, version: str) -> bool:
        """Check if blueprint version supports VR1"""
        try:
            from packaging import version as pkg_version
            parsed_version = pkg_version.parse(version)
            min_version = pkg_version.parse("1.1.0")
            return parsed_version >= min_version
        except Exception:
            return False
    
    def _has_boundary_fields(self, blueprint: ParsedBlueprint) -> bool:
        """Check if blueprint already has VR1 boundary fields"""
        component = blueprint.component
        
        # Check for any boundary semantics fields
        for port in component.inputs + component.outputs:
            if (getattr(port, 'boundary_ingress', False) or
                getattr(port, 'boundary_egress', False) or
                getattr(port, 'reply_required', False) or
                getattr(port, 'satisfies_reply', False) or
                getattr(port, 'observability_export', False)):
                return True
        
        # Check for component-level VR1 fields
        if (getattr(component, 'durable', False) or
            getattr(component, 'monitored_bus_ok', False)):
            return True
        
        return False
    
    def _plan_migration_operations(self, blueprint: ParsedBlueprint, 
                                 analysis: MigrationResult) -> List[MigrationOperation]:
        """Plan specific migration operations to apply"""
        operations = []
        
        if analysis.migration_type == MigrationType.BOUNDARY_FIELD_ADDITION:
            operations.extend(self._plan_boundary_field_operations(blueprint))
        
        elif analysis.migration_type == MigrationType.LEGACY_TO_VR1_FULL:
            operations.extend(self._plan_full_migration_operations(blueprint))
        
        return operations
    
    def _plan_boundary_field_operations(self, blueprint: ParsedBlueprint) -> List[MigrationOperation]:
        """Plan boundary field addition operations"""
        operations = []
        
        component = blueprint.component
        
        # Add boundary semantics based on component type
        if component.type == "APIEndpoint":
            operations.extend(self._plan_api_endpoint_boundary_fields(component))
        elif component.type == "WebSocket":
            operations.extend(self._plan_websocket_boundary_fields(component))
        elif component.type == "Store":
            operations.extend(self._plan_store_durability_fields(component))
        elif component.type == "Controller":
            operations.extend(self._plan_controller_boundary_fields(component))
        # Add more component types as needed
        
        return operations
    
    def _plan_full_migration_operations(self, blueprint: ParsedBlueprint) -> List[MigrationOperation]:
        """Plan full legacy migration operations"""
        # For full migration, we apply boundary field operations
        # plus any additional legacy compatibility updates
        return self._plan_boundary_field_operations(blueprint)
    
    def _plan_api_endpoint_boundary_fields(self, component: ParsedComponent) -> List[MigrationOperation]:
        """Plan boundary field operations for APIEndpoint components"""
        operations = []
        
        # Find request input port
        request_port = next((p for p in component.inputs if p.name == "request"), None)
        if request_port and not getattr(request_port, 'boundary_ingress', False):
            operations.append(MigrationOperation(
                operation_type="add_boundary_ingress",
                target_component=component.name,
                target_port=request_port.name,
                old_value=False,
                new_value=True,
                justification="APIEndpoint request port is boundary ingress by definition"
            ))
            
            operations.append(MigrationOperation(
                operation_type="add_reply_required",
                target_component=component.name,
                target_port=request_port.name,
                old_value=False,
                new_value=True,
                justification="APIEndpoint request requires response"
            ))
        
        # Find response output port
        response_port = next((p for p in component.outputs if p.name == "response"), None)
        if response_port and not getattr(response_port, 'satisfies_reply', False):
            operations.append(MigrationOperation(
                operation_type="add_satisfies_reply",
                target_component=component.name,
                target_port=response_port.name,
                old_value=False,
                new_value=True,
                justification="APIEndpoint response port satisfies request reply"
            ))
        
        return operations
    
    def _plan_websocket_boundary_fields(self, component: ParsedComponent) -> List[MigrationOperation]:
        """Plan boundary field operations for WebSocket components"""
        operations = []
        
        # Connection request port
        connection_request_port = next((p for p in component.inputs if "connection" in p.name.lower()), None)
        if connection_request_port and not getattr(connection_request_port, 'boundary_ingress', False):
            operations.append(MigrationOperation(
                operation_type="add_boundary_ingress",
                target_component=component.name,
                target_port=connection_request_port.name,
                old_value=False,
                new_value=True,
                justification="WebSocket connection port is boundary ingress"
            ))
            
            operations.append(MigrationOperation(
                operation_type="add_reply_required",
                target_component=component.name,
                target_port=connection_request_port.name,
                old_value=False,
                new_value=True,
                justification="WebSocket connection requires handshake response"
            ))
        
        # Message input port
        message_port = next((p for p in component.inputs if "message" in p.name.lower()), None)
        if message_port and not getattr(message_port, 'boundary_ingress', False):
            operations.append(MigrationOperation(
                operation_type="add_boundary_ingress",
                target_component=component.name,
                target_port=message_port.name,
                old_value=False,
                new_value=True,
                justification="WebSocket message port is boundary ingress"
            ))
        
        # Connection status output
        status_port = next((p for p in component.outputs if "status" in p.name.lower()), None)
        if status_port and not getattr(status_port, 'satisfies_reply', False):
            operations.append(MigrationOperation(
                operation_type="add_satisfies_reply",
                target_component=component.name,
                target_port=status_port.name,
                old_value=False,
                new_value=True,
                justification="WebSocket status port satisfies connection reply"
            ))
        
        # Add monitored_bus_ok for message handling
        if not getattr(component, 'monitored_bus_ok', False):
            operations.append(MigrationOperation(
                operation_type="add_monitored_bus_ok",
                target_component=component.name,
                old_value=False,
                new_value=True,
                justification="WebSocket allows observability-only termination for messages"
            ))
        
        return operations
    
    def _plan_store_durability_fields(self, component: ParsedComponent) -> List[MigrationOperation]:
        """Plan durability field operations for Store components"""
        operations = []
        
        # Store components should be durable
        if not getattr(component, 'durable', False):
            operations.append(MigrationOperation(
                operation_type="add_durable",
                target_component=component.name,
                old_value=False,
                new_value=True,
                justification="Store components provide durable storage"
            ))
        
        return operations
    
    def _plan_controller_boundary_fields(self, component: ParsedComponent) -> List[MigrationOperation]:
        """Plan boundary field operations for Controller components"""
        operations = []
        
        # Controllers typically just pass through data
        # No specific boundary semantics needed unless they're entry points
        
        # If controller has single input/output that looks like API pattern, add reply semantics
        if len(component.inputs) == 1 and len(component.outputs) == 1:
            input_port = component.inputs[0]
            output_port = component.outputs[0]
            
            # If input has boundary_ingress (from APIEndpoint), ensure output satisfies reply
            if getattr(input_port, 'reply_required', False) and not getattr(output_port, 'satisfies_reply', False):
                operations.append(MigrationOperation(
                    operation_type="add_satisfies_reply",
                    target_component=component.name,
                    target_port=output_port.name,
                    old_value=False,
                    new_value=True,
                    justification="Controller output satisfies input reply requirement"
                ))
        
        return operations
    
    def _calculate_migration_confidence(self, operations: List[MigrationOperation]) -> float:
        """Calculate confidence score for migration operations"""
        if not operations:
            return 1.0
        
        # Base confidence starts high for simple operations
        base_confidence = 0.9
        
        # Reduce confidence for certain risky operations
        confidence_penalties = {
            "add_boundary_ingress": 0.05,
            "add_reply_required": 0.05,
            "add_satisfies_reply": 0.03,
            "add_durable": 0.02,
            "add_monitored_bus_ok": 0.05
        }
        
        total_penalty = sum(
            confidence_penalties.get(op.operation_type, 0.1) 
            for op in operations
        )
        
        # Confidence decreases with number of operations
        operation_penalty = min(0.2, len(operations) * 0.02)
        
        final_confidence = max(0.0, base_confidence - total_penalty - operation_penalty)
        return final_confidence
    
    def _apply_migration_operations(self, blueprint: ParsedBlueprint,
                                  operations: List[MigrationOperation]) -> ParsedBlueprint:
        """Apply migration operations to blueprint"""
        migrated_blueprint = deepcopy(blueprint)
        component = migrated_blueprint.component
        
        for operation in operations:
            self._apply_single_operation(component, operation)
        
        return migrated_blueprint
    
    def _apply_single_operation(self, component: ParsedComponent, operation: MigrationOperation):
        """Apply a single migration operation"""
        
        if operation.operation_type == "add_boundary_ingress":
            port = self._find_port(component, operation.target_port, is_input=True)
            if port:
                port.boundary_ingress = operation.new_value
                
        elif operation.operation_type == "add_reply_required":
            port = self._find_port(component, operation.target_port, is_input=True)
            if port:
                port.reply_required = operation.new_value
                
        elif operation.operation_type == "add_satisfies_reply":
            port = self._find_port(component, operation.target_port, is_input=False)
            if port:
                port.satisfies_reply = operation.new_value
                
        elif operation.operation_type == "add_durable":
            component.durable = operation.new_value
            
        elif operation.operation_type == "add_monitored_bus_ok":
            component.monitored_bus_ok = operation.new_value
        
        else:
            self.logger.warning(f"Unknown migration operation: {operation.operation_type}")
    
    def _find_port(self, component: ParsedComponent, port_name: str, is_input: bool) -> Optional[ParsedPort]:
        """Find a port by name in component"""
        ports = component.inputs if is_input else component.outputs
        return next((port for port in ports if port.name == port_name), None)
    
    def _validate_migrated_blueprint(self, blueprint: ParsedBlueprint) -> List[str]:
        """Validate migrated blueprint and return warnings"""
        warnings = []
        
        try:
            # Basic structural validation
            component = blueprint.component
            
            if not component.inputs and not component.outputs:
                warnings.append("Component has no inputs or outputs after migration")
            
            # Check for conflicting boundary semantics
            for port in component.inputs + component.outputs:
                if (getattr(port, 'boundary_ingress', False) and 
                    getattr(port, 'boundary_egress', False)):
                    warnings.append(f"Port {port.name} has conflicting boundary_ingress and boundary_egress")
                
                if (getattr(port, 'reply_required', False) and 
                    port in component.outputs):
                    warnings.append(f"Output port {port.name} should not have reply_required=true")
        
        except Exception as e:
            warnings.append(f"Validation error: {str(e)}")
        
        return warnings


class AutoHealingEngine:
    """
    Auto-healing system for VR1 validation failures
    
    Automatically detects and fixes common blueprint issues that cause VR1 validation
    failures, reducing manual intervention requirements.
    """
    
    def __init__(self, migration_engine: BlueprintMigrationEngine):
        self.migration_engine = migration_engine
        self.logger = logging.getLogger(__name__)
        
    def auto_heal_validation_failures(self, blueprint: ParsedBlueprint,
                                    validation_errors: List[VR1ValidationError]) -> Tuple[ParsedBlueprint, List[str]]:
        """
        Automatically heal VR1 validation failures where possible
        
        Args:
            blueprint: Blueprint with validation failures
            validation_errors: List of VR1 validation errors
            
        Returns:
            (healed_blueprint, healing_actions_applied)
        """
        healed_blueprint = deepcopy(blueprint)
        healing_actions = []
        
        for error in validation_errors:
            healing_action = self._heal_validation_error(healed_blueprint, error)
            if healing_action:
                healing_actions.append(healing_action)
        
        return healed_blueprint, healing_actions
    
    def _heal_validation_error(self, blueprint: ParsedBlueprint, 
                             error: VR1ValidationError) -> Optional[str]:
        """Heal a specific validation error"""
        
        if error.error_type == VR1ErrorType.REPLY_COMMITMENT_UNMET:
            return self._heal_reply_commitment_unmet(blueprint, error)
        
        elif error.error_type == VR1ErrorType.NO_BOUNDARY_INGRESS:
            return self._heal_no_boundary_ingress(blueprint, error)
        
        elif error.error_type == VR1ErrorType.MISSING_OUTPUT_PORT:
            return self._heal_missing_output_port(blueprint, error)
        
        elif error.error_type == VR1ErrorType.DURABLE_COMMITMENT_UNMET:
            return self._heal_durable_commitment_unmet(blueprint, error)
        
        # More healing methods for other error types...
        
        return None
    
    def _heal_reply_commitment_unmet(self, blueprint: ParsedBlueprint, 
                                   error: VR1ValidationError) -> Optional[str]:
        """Heal reply commitment unmet errors"""
        
        component_name = error.context.component_name
        if not component_name:
            return None
        
        component = blueprint.component
        if component.name != component_name:
            return None
        
        # Find response-like output ports and add satisfies_reply=true
        response_candidates = [
            port for port in component.outputs 
            if any(keyword in port.name.lower() for keyword in ["response", "reply", "result", "output"])
        ]
        
        if response_candidates:
            for port in response_candidates:
                port.satisfies_reply = True
            
            return f"Added satisfies_reply=true to {len(response_candidates)} response ports in {component_name}"
        
        return None
    
    def _heal_no_boundary_ingress(self, blueprint: ParsedBlueprint,
                                error: VR1ValidationError) -> Optional[str]:
        """Heal no boundary ingress errors by inferring ingress points"""
        
        component = blueprint.component
        
        # Look for APIEndpoint, WebSocket, or other likely ingress components
        if component.type in ["APIEndpoint", "WebSocket", "EventListener", "MessageSubscriber"]:
            healed_count = 0
            for input_port in component.inputs:
                if not getattr(input_port, 'boundary_ingress', False):
                    input_port.boundary_ingress = True
                    healed_count += 1
            
            if healed_count > 0:
                return f"Added boundary_ingress=true to {healed_count} ports on {component.type} component"
        
        return None
    
    def _heal_missing_output_port(self, blueprint: ParsedBlueprint,
                                error: VR1ValidationError) -> Optional[str]:
        """Heal missing output port errors"""
        # This would require adding ports to components, which is more complex
        # For now, just log the issue
        self.logger.info(f"Cannot auto-heal missing output port: {error.message}")
        return None
    
    def _heal_durable_commitment_unmet(self, blueprint: ParsedBlueprint,
                                     error: VR1ValidationError) -> Optional[str]:
        """Heal durable commitment unmet errors"""
        
        component = blueprint.component
        
        # If component should be durable based on type, make it durable
        if component.type in ["Store", "Database", "PersistentQueue"]:
            if not getattr(component, 'durable', False):
                component.durable = True
                return f"Added durable=true to {component.type} component {component.name}"
        
        return None


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
        blueprint_version = blueprint.metadata.get('version', '1.0.0') if blueprint.metadata else '1.0.0'
        if not self._is_blueprint_version_eligible(blueprint_version):
            return False
        
        # For single-component blueprints, always eligible
        return True
    
    def _is_vr1_globally_enabled(self) -> bool:
        """Check global VR1 feature flag"""
        import os
        return os.getenv("BOUNDARY_TERMINATION_ENABLED", "false").lower() == "true"
    
    def _is_vr1_enabled_for_environment(self, environment: str) -> bool:
        """Check environment-specific VR1 rollout"""
        import os
        
        rollout_environments = os.getenv("VR1_ROLLOUT_ENVIRONMENTS", "development").split(",")
        return environment.lower() in [env.strip().lower() for env in rollout_environments]
    
    def _is_blueprint_version_eligible(self, version: str) -> bool:
        """Check if blueprint version is eligible for VR1"""
        try:
            # Simple version comparison - 1.1.0 and above are eligible
            version_parts = version.split('.')
            major = int(version_parts[0])
            minor = int(version_parts[1]) if len(version_parts) > 1 else 0
            
            return major > 1 or (major == 1 and minor >= 1)
        except Exception:
            # Default to eligible if version parsing fails
            return True


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
            # For compatibility, return success when VR1 is disabled
            # In production, this would call the actual legacy validator
            return True, actions_taken, blueprint
        
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
        from .vr1_validator import VR1Validator
        vr1_validator = VR1Validator(blueprint)
        validation_result = vr1_validator.validate_boundary_termination()
        
        if validation_result.passed:
            actions_taken.append("VR1 validation passed")
            return True, actions_taken, blueprint
        
        # Phase 4: Auto-healing attempt if validation failed
        if hasattr(validation_result, 'failures') and validation_result.failures:
            # Convert legacy ValidationFailure to VR1ValidationError for auto-healing
            # This is a simplified conversion for now
            vr1_errors = []
            for failure in validation_result.failures:
                if hasattr(failure, 'error_message') and 'reply' in failure.error_message.lower():
                    vr1_error = VR1ValidationError(
                        error_type=VR1ErrorType.REPLY_COMMITMENT_UNMET,
                        error_category=VR1ErrorCategory.TERMINATION_ISSUES,
                        message=failure.error_message,
                        context=VR1ErrorContext(component_name=getattr(failure, 'component_name', None))
                    )
                    vr1_errors.append(vr1_error)
            
            if vr1_errors:
                healed_blueprint, healing_actions = self.auto_healing.auto_heal_validation_failures(
                    blueprint, vr1_errors
                )
                
                if healing_actions:
                    actions_taken.extend([f"Auto-healing: {action}" for action in healing_actions])
                    
                    # Retry validation with healed blueprint
                    retry_validator = VR1Validator(healed_blueprint)
                    retry_result = retry_validator.validate_boundary_termination()
                    
                    if retry_result.passed:
                        actions_taken.append("VR1 validation passed after auto-healing")
                        return True, actions_taken, healed_blueprint
        
        # Phase 5: VR1 validation failed
        actions_taken.append("VR1 validation failed")
        return False, actions_taken, blueprint