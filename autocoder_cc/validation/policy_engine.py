from __future__ import annotations

from autocoder_cc.observability.structured_logging import get_logger
from tests.contracts.blueprint_structure_contract import BlueprintContract
"""policy_engine.py – Production-Ready Constraint-as-Code evaluator with fail-hard enforcement.

This engine inspects a blueprint YAML file looking for a top-level
`policy` block as described in the Enterprise Roadmap Phase 2.5.
It evaluates constraint rules with fail-hard enforcement:

* `slos`: numeric service-level objectives (e.g. p95_latency_ms) – must be positive.
* `resource_limits`: CPU and memory limits – must not exceed thresholds.
* `disallowed_dependencies`: list of package names that must not appear in `components[*].dependencies`.
* `security_constraints`: security policy enforcement for components.
* `validation_rules`: custom constraint expressions using ConstraintValidator.

Policy violations result in hard failures with no fallback mechanisms.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml

# Production thresholds - configurable per deployment
DEFAULT_MAX_CPU = 4  # cores
DEFAULT_MAX_MEM_MB = 8192  # MB

class ConstraintViolation:
    """Represents a policy constraint violation with enhanced context."""
    
    def __init__(self, message: str, path: str, severity: str = "error", 
                 constraint_type: str = "policy", component: Optional[str] = None):
        self.message = message
        self.path = path
        self.severity = severity  # error, warning, info
        self.constraint_type = constraint_type  # policy, resource, security, custom
        self.component = component

    def __str__(self) -> str:
        comp_str = f" ({self.component})" if self.component else ""
        return f"[{self.severity.upper()}] {self.constraint_type}:{self.path}{comp_str}: {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert violation to dictionary for structured logging."""
        return {
            "message": self.message,
            "path": self.path,
            "severity": self.severity,
            "constraint_type": self.constraint_type,
            "component": self.component
        }

class ConstraintEvaluator:
    """
    Production-ready constraint evaluator with fail-hard enforcement.
    
    Integrates with ConstraintValidator for sophisticated constraint evaluation
    and provides comprehensive policy violation handling.
    """
    
    def __init__(self, blueprint_path: str | Path, max_cpu: int = DEFAULT_MAX_CPU, 
                 max_memory_mb: int = DEFAULT_MAX_MEM_MB):
        self.path = Path(blueprint_path)
        self.max_cpu = max_cpu
        self.max_memory_mb = max_memory_mb
        self.logger = get_logger("ConstraintEvaluator")
        
        if not self.path.exists():
            raise FileNotFoundError(f"Blueprint file not found: {self.path}")
        
        try:
            with self.path.open("r", encoding="utf-8") as f:
                self.blueprint: Dict[str, Any] = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in blueprint file {self.path}: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load blueprint file {self.path}: {e}")
        
        # Initialize constraint validator for custom rules
        from ..validation import ConstraintValidator
        self.constraint_validator = ConstraintValidator()

    def evaluate(self) -> List[ConstraintViolation]:
        """
        Evaluate all policy constraints with fail-hard enforcement.
        
        Returns list of violations. Any ERROR-level violations should cause
        hard failure with no fallback mechanisms.
        """
        violations: List[ConstraintViolation] = []
        policy = self.blueprint.get("policy") if "policy" in self.blueprint else self.blueprint.get("system", {}).get("policy")
        
        if not policy:
            # Policy block is optional for backwards compatibility, but log warning
            self.logger.warning("No policy block found in blueprint - policy validation skipped")
            return violations

        self.logger.info(f"Evaluating policy constraints from {self.path}")

        # 1. SLOs - Service Level Objectives
        violations.extend(self._evaluate_slos(policy))
        
        # 2. Resource limits
        violations.extend(self._evaluate_resource_limits(policy))
        
        # 3. Disallowed dependencies  
        violations.extend(self._evaluate_disallowed_dependencies(policy))
        
        # 4. Security constraints (NEW)
        violations.extend(self._evaluate_security_constraints(policy))
        
        # 5. Custom validation rules using ConstraintValidator (NEW)
        violations.extend(self._evaluate_custom_constraints(policy))
        
        # Log violations for monitoring
        error_count = len([v for v in violations if v.severity == "error"])
        warning_count = len([v for v in violations if v.severity == "warning"])
        
        if error_count > 0:
            self.logger.error(f"Policy evaluation failed: {error_count} errors, {warning_count} warnings")
            for violation in violations:
                if violation.severity == "error":
                    self.logger.error(f"POLICY VIOLATION: {violation}")
        elif warning_count > 0:
            self.logger.warning(f"Policy evaluation completed: {warning_count} warnings")
        else:
            self.logger.info("✅ All policy constraints passed")
        
        return violations
    
    def _evaluate_slos(self, policy: Dict[str, Any]) -> List[ConstraintViolation]:
        """Evaluate Service Level Objectives."""
        violations = []
        slos = policy.get("slos", {})
        
        for slo_name, value in slos.items():
            if not isinstance(value, (int, float)):
                violations.append(ConstraintViolation(
                    f"SLO '{slo_name}' must be a number, got {type(value).__name__}",
                    f"policy.slos.{slo_name}",
                    severity="error",
                    constraint_type="slo"
                ))
            elif value <= 0:
                violations.append(ConstraintViolation(
                    f"SLO '{slo_name}' must be positive, got {value}",
                    f"policy.slos.{slo_name}",
                    severity="error", 
                    constraint_type="slo"
                ))
        
        return violations
    
    def _evaluate_resource_limits(self, policy: Dict[str, Any]) -> List[ConstraintViolation]:
        """Evaluate resource limit constraints."""
        violations = []
        rl = policy.get("resource_limits", {})
        
        cpu = rl.get("cpu_cores")
        mem = rl.get("memory_mb")
        
        if cpu is not None:
            if not isinstance(cpu, (int, float)) or cpu <= 0:
                violations.append(ConstraintViolation(
                    f"CPU cores must be positive number, got {cpu}",
                    "policy.resource_limits.cpu_cores",
                    severity="error",
                    constraint_type="resource"
                ))
            elif cpu > self.max_cpu:
                violations.append(ConstraintViolation(
                    f"CPU cores {cpu} exceed maximum allowed {self.max_cpu}",
                    "policy.resource_limits.cpu_cores",
                    severity="error",
                    constraint_type="resource"
                ))
        
        if mem is not None:
            if not isinstance(mem, (int, float)) or mem <= 0:
                violations.append(ConstraintViolation(
                    f"Memory must be positive number, got {mem}",
                    "policy.resource_limits.memory_mb", 
                    severity="error",
                    constraint_type="resource"
                ))
            elif mem > self.max_memory_mb:
                violations.append(ConstraintViolation(
                    f"Memory {mem}MB exceeds maximum allowed {self.max_memory_mb}MB",
                    "policy.resource_limits.memory_mb",
                    severity="error",
                    constraint_type="resource"
                ))
        
        return violations
    
    def _evaluate_disallowed_dependencies(self, policy: Dict[str, Any]) -> List[ConstraintViolation]:
        """Evaluate disallowed dependency constraints."""
        violations = []
        disallowed = set(policy.get("disallowed_dependencies", []))
        
        if disallowed:
            components = BlueprintContract.get_components(self.blueprint)
            for idx, comp in enumerate(components):
                comp_name = comp.get("name", f"component[{idx}]")
                deps = set(comp.get("dependencies", []))
                banned = deps & disallowed
                
                if banned:
                    violations.append(ConstraintViolation(
                        f"Component uses disallowed dependencies: {', '.join(sorted(banned))}",
                        f"components[{idx}].dependencies",
                        severity="error",
                        constraint_type="dependency",
                        component=comp_name
                    ))
        
        return violations
    
    def _evaluate_security_constraints(self, policy: Dict[str, Any]) -> List[ConstraintViolation]:
        """Evaluate security policy constraints."""
        violations = []
        security = policy.get("security_constraints", {})
        
        # Require encrypted communication
        if security.get("require_encryption", False):
            components = BlueprintContract.get_components(self.blueprint)
            for idx, comp in enumerate(components):
                comp_name = comp.get("name", f"component[{idx}]")
                config = comp.get("configuration", {})
                
                # Check for unencrypted URLs
                for key, value in config.items():
                    if isinstance(value, str) and value.startswith("http://"):
                        violations.append(ConstraintViolation(
                            f"Unencrypted HTTP URL not allowed when encryption required: {key}={value}",
                            f"components[{idx}].configuration.{key}",
                            severity="error",
                            constraint_type="security",
                            component=comp_name
                        ))
        
        # Disallow privileged execution
        if security.get("disallow_privileged", False):
            components = BlueprintContract.get_components(self.blueprint)
            for idx, comp in enumerate(components):
                comp_name = comp.get("name", f"component[{idx}]")
                config = comp.get("configuration", {})
                
                if config.get("privileged", False) or config.get("run_as_root", False):
                    violations.append(ConstraintViolation(
                        "Privileged execution not allowed by security policy",
                        f"components[{idx}].configuration",
                        severity="error",
                        constraint_type="security",
                        component=comp_name
                    ))
        
        return violations
    
    def _evaluate_custom_constraints(self, policy: Dict[str, Any]) -> List[ConstraintViolation]:
        """Evaluate custom constraint expressions using ConstraintValidator."""
        violations = []
        custom_rules = policy.get("validation_rules", [])
        
        for rule_idx, rule in enumerate(custom_rules):
            if not isinstance(rule, dict):
                violations.append(ConstraintViolation(
                    f"Validation rule must be object, got {type(rule).__name__}",
                    f"policy.validation_rules[{rule_idx}]",
                    severity="error",
                    constraint_type="custom"
                ))
                continue
            
            expression = rule.get("expression", "")
            description = rule.get("description", f"Custom rule {rule_idx}")
            severity = rule.get("severity", "error")
            
            if not expression:
                violations.append(ConstraintViolation(
                    "Validation rule missing expression",
                    f"policy.validation_rules[{rule_idx}].expression",
                    severity="error",
                    constraint_type="custom"
                ))
                continue
            
            # Create context with blueprint data for constraint evaluation
            context = {
                "blueprint": self.blueprint,
                "components": BlueprintContract.get_components(self.blueprint),
                "policy": policy
            }
            
            try:
                # Use ConstraintValidator to evaluate the expression
                result = self.constraint_validator.validate_constraint(
                    context, expression, f"custom_rule[{rule_idx}]", "policy_engine"
                )
                
                # Convert validation errors to constraint violations
                for error in result.get_all_issues():
                    violations.append(ConstraintViolation(
                        f"{description}: {error.message}",
                        f"policy.validation_rules[{rule_idx}]",
                        severity=severity,
                        constraint_type="custom"
                    ))
                    
            except Exception as e:
                violations.append(ConstraintViolation(
                    f"Failed to evaluate custom constraint '{expression}': {e}",
                    f"policy.validation_rules[{rule_idx}].expression",
                    severity="error",
                    constraint_type="custom"
                ))
        
        return violations


def main() -> None:  # simple CLI
    import argparse
    ap = argparse.ArgumentParser(description="Validate blueprint against policy block")
    ap.add_argument("blueprint", help="Path to blueprint YAML")
    args = ap.parse_args()

    evaluator = ConstraintEvaluator(args.blueprint)
    violations = evaluator.evaluate()
    if violations:
        print("❌ Violations detected:")
        for v in violations:
            print(" -", v)
        sys.exit(1)
    print("✅ Policy checks passed")

if __name__ == "__main__":
    main() 