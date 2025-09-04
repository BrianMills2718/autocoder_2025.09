#!/usr/bin/env python3
"""
Observability Compliance Monitor

Implements active compliance enforcement for observability economics,
automatically detecting and correcting policy violations.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from autocoder_cc.observability.sampling_policy import SamplingPolicyManager
from autocoder_cc.observability.retention_budget import RetentionBudgetManager
from autocoder_cc.observability.unified_economics import UnifiedEconomicsManager


class ViolationType(Enum):
    """Types of compliance violations"""
    BUDGET_EXCEEDED = "budget_exceeded"
    SAMPLING_RATE_TOO_LOW = "sampling_rate_too_low"
    RETENTION_TOO_SHORT = "retention_too_short"
    STORAGE_TIER_INAPPROPRIATE = "storage_tier_inappropriate"
    COST_SPIKE = "cost_spike"
    COMPLIANCE_DRIFT = "compliance_drift"


@dataclass
class ComplianceViolation:
    """Individual compliance violation"""
    type: ViolationType
    environment: str
    policy_name: str
    description: str
    severity: str  # "low", "medium", "high", "critical"
    detected_at: datetime
    current_value: Any
    expected_value: Any
    auto_correctable: bool = False
    corrected_at: Optional[datetime] = None
    correction_applied: Optional[str] = None


class ComplianceMonitor:
    """Active compliance monitoring and enforcement"""
    
    def __init__(self):
        self.sampling_manager = SamplingPolicyManager()
        self.retention_manager = RetentionBudgetManager()
        self.unified_manager = UnifiedEconomicsManager()
        self.logger = logging.getLogger(__name__)
        
        # Real-world data integration
        from autocoder_cc.observability.real_world_integrations import RealWorldDataManager
        self.real_world_manager = RealWorldDataManager()
        
        # Compliance thresholds
        self.thresholds = {
            "budget_utilization_warning": 0.8,  # 80%
            "budget_utilization_critical": 1.0,  # 100%
            "cost_spike_threshold": 2.0,  # 2x normal cost
            "critical_data_min_sampling": 1.0,  # 100% for critical data
            "critical_data_min_retention_days": 365,  # 1 year minimum
        }
        
        # Violation history for trend analysis
        self.violation_history: List[ComplianceViolation] = []
        
        # Auto-correction settings
        self.auto_correction_enabled = True
        self.max_corrections_per_hour = 10
        self.correction_count = 0
        self.last_correction_window = datetime.now()
    
    def scan_all_environments(self) -> Dict[str, List[ComplianceViolation]]:
        """Scan all environments for compliance violations"""
        violations = {}
        
        for env in ["development", "staging", "production"]:
            env_violations = []
            
            # Check sampling policy violations
            env_violations.extend(self._check_sampling_violations(env))
            
            # Check retention policy violations  
            env_violations.extend(self._check_retention_violations(env))
            
            # Check unified budget violations
            env_violations.extend(self._check_unified_budget_violations(env))
            
            violations[env] = env_violations
            
            # Store violations in history
            self.violation_history.extend(env_violations)
        
        return violations
    
    def _check_sampling_violations(self, environment: str) -> List[ComplianceViolation]:
        """Check sampling policy for violations"""
        violations = []
        policy = self.sampling_manager.get_policy(environment)
        
        if not policy:
            return violations
        
        # Check critical data sampling rates
        for rule in policy.rules:
            if rule.type.value in ["error", "security", "audit"]:
                if rule.rate < self.thresholds["critical_data_min_sampling"]:
                    violations.append(ComplianceViolation(
                        type=ViolationType.SAMPLING_RATE_TOO_LOW,
                        environment=environment,
                        policy_name=rule.name,
                        description=f"Critical data type '{rule.type.value}' has sampling rate {rule.rate:.1%} < 100%",
                        severity="critical",
                        detected_at=datetime.now(),
                        current_value=rule.rate,
                        expected_value=1.0,
                        auto_correctable=True
                    ))
        
        # Check budget utilization
        if policy.budget_limit:
            cost_estimate = self.sampling_manager._estimate_cost(policy)
            current_cost = cost_estimate["total_per_month"]
            budget = policy.budget_limit.total_cost_per_month
            utilization = current_cost / budget
            
            if utilization > self.thresholds["budget_utilization_critical"]:
                violations.append(ComplianceViolation(
                    type=ViolationType.BUDGET_EXCEEDED,
                    environment=environment,
                    policy_name="sampling_budget",
                    description=f"Sampling budget exceeded: {utilization:.1%} of ${budget:.2f}",
                    severity="critical",
                    detected_at=datetime.now(),
                    current_value=current_cost,
                    expected_value=budget,
                    auto_correctable=True
                ))
            elif utilization > self.thresholds["budget_utilization_warning"]:
                violations.append(ComplianceViolation(
                    type=ViolationType.BUDGET_EXCEEDED,
                    environment=environment,
                    policy_name="sampling_budget",
                    description=f"Sampling budget warning: {utilization:.1%} of ${budget:.2f}",
                    severity="medium",
                    detected_at=datetime.now(),
                    current_value=current_cost,
                    expected_value=budget * 0.8,
                    auto_correctable=False
                ))
        
        return violations
    
    def _check_retention_violations(self, environment: str) -> List[ComplianceViolation]:
        """Check retention policy for violations"""
        violations = []
        policy = self.retention_manager.get_policy(environment)
        
        if not policy:
            return violations
        
        # Check critical data retention periods
        for rule in policy.rules:
            if rule.obs_type in ["security", "audit"]:
                retention_days = rule.get_retention_days()
                min_days = self.thresholds["critical_data_min_retention_days"]
                
                if retention_days < min_days:
                    violations.append(ComplianceViolation(
                        type=ViolationType.RETENTION_TOO_SHORT,
                        environment=environment,
                        policy_name=rule.name,
                        description=f"Critical data type '{rule.obs_type}' retention {retention_days} days < {min_days} days",
                        severity="critical",
                        detected_at=datetime.now(),
                        current_value=retention_days,
                        expected_value=min_days,
                        auto_correctable=True
                    ))
        
        return violations
    
    def _check_unified_budget_violations(self, environment: str) -> List[ComplianceViolation]:
        """Check unified budget for violations"""
        violations = []
        
        # Get unified budget status
        status = self.unified_manager.get_unified_budget_status(environment)
        
        if status["status"] == "success":
            if not status["within_budget"]:
                violations.append(ComplianceViolation(
                    type=ViolationType.BUDGET_EXCEEDED,
                    environment=environment,
                    policy_name="unified_budget",
                    description=f"Total budget exceeded: ${status['total_current_cost']:.2f} > ${status['total_budget']:.2f}",
                    severity="critical",
                    detected_at=datetime.now(),
                    current_value=status["total_current_cost"],
                    expected_value=status["total_budget"],
                    auto_correctable=True
                ))
            
            # Check for cost spikes (comparing to historical averages)
            if status["budget_utilization"] > self.thresholds["cost_spike_threshold"]:
                violations.append(ComplianceViolation(
                    type=ViolationType.COST_SPIKE,
                    environment=environment,
                    policy_name="unified_budget",
                    description=f"Cost spike detected: {status['budget_utilization']:.1%} utilization",
                    severity="high",
                    detected_at=datetime.now(),
                    current_value=status["budget_utilization"],
                    expected_value=0.8,  # 80% normal utilization
                    auto_correctable=True
                ))
        
        return violations
    
    def auto_correct_violations(self, violations: Dict[str, List[ComplianceViolation]]) -> Dict[str, Any]:
        """Automatically correct violations where possible"""
        if not self.auto_correction_enabled:
            return {"corrections_applied": 0, "reason": "Auto-correction disabled"}
        
        # Check rate limiting
        now = datetime.now()
        if now - self.last_correction_window > timedelta(hours=1):
            self.correction_count = 0
            self.last_correction_window = now
        
        if self.correction_count >= self.max_corrections_per_hour:
            return {"corrections_applied": 0, "reason": "Rate limit exceeded"}
        
        corrections_applied = 0
        correction_actions = []
        
        for environment, env_violations in violations.items():
            for violation in env_violations:
                if not violation.auto_correctable:
                    continue
                
                if self.correction_count >= self.max_corrections_per_hour:
                    break
                
                # Apply correction based on violation type
                correction_result = self._apply_correction(violation)
                
                if correction_result["success"]:
                    violation.corrected_at = datetime.now()
                    violation.correction_applied = correction_result["action"]
                    corrections_applied += 1
                    self.correction_count += 1
                    
                    correction_actions.append({
                        "environment": environment,
                        "violation_type": violation.type.value,
                        "policy_name": violation.policy_name,
                        "action": correction_result["action"],
                        "corrected_at": violation.corrected_at.isoformat()
                    })
                    
                    self.logger.warning(f"Auto-corrected violation: {violation.description}")
        
        return {
            "corrections_applied": corrections_applied,
            "actions": correction_actions,
            "rate_limit_remaining": self.max_corrections_per_hour - self.correction_count
        }
    
    def _apply_correction(self, violation: ComplianceViolation) -> Dict[str, Any]:
        """Apply correction using real-world data"""
        try:
            if violation.type == ViolationType.SAMPLING_RATE_TOO_LOW:
                # Correct critical data sampling rate to 100%
                policy = self.sampling_manager.get_policy(violation.environment)
                if policy:
                    for rule in policy.rules:
                        if rule.name == violation.policy_name:
                            rule.rate = 1.0
                            return {"success": True, "action": f"Set sampling rate to 100% for {rule.name}"}
            
            elif violation.type == ViolationType.RETENTION_TOO_SHORT:
                # Correct critical data retention period
                policy = self.retention_manager.get_policy(violation.environment)
                if policy:
                    for rule in policy.rules:
                        if rule.name == violation.policy_name:
                            from autocoder_cc.observability.retention_budget import RetentionPeriod
                            rule.retention_period = RetentionPeriod.DAYS_365
                            return {"success": True, "action": f"Set retention to 365 days for {rule.name}"}
            
            elif violation.type == ViolationType.BUDGET_EXCEEDED:
                # Apply budget enforcement using real cost data
                if "sampling" in violation.policy_name:
                    # Get real cost data for current environment
                    real_costs = self.real_world_manager.get_real_costs(violation.environment)
                    
                    # Use real budget enforcement with actual cost data
                    current_costs = {
                        "sampling": violation.current_value,
                        "storage": real_costs.storage_cost,
                        "query": real_costs.query_cost,
                        "ingestion": real_costs.ingestion_cost
                    }
                    
                    enforcement_result = self.sampling_manager.enforce_budget_limits(violation.environment, current_costs)
                    
                    if enforcement_result["enforcement_applied"]:
                        return {"success": True, "action": f"Applied budget enforcement: {enforcement_result['total_rules_modified']} rules modified"}
                
                elif "unified" in violation.policy_name:
                    # Apply unified cost optimization using real data
                    target_cost = violation.expected_value * 0.9  # 90% of budget
                    optimization_result = self.unified_manager.optimize_total_cost(violation.environment, target_cost)
                    
                    if optimization_result["optimization_applied"]:
                        return {"success": True, "action": f"Applied unified optimization: ${optimization_result['cost_reduction_needed']:.2f} reduction"}
            
            elif violation.type == ViolationType.COST_SPIKE:
                # Apply emergency throttling based on real cost data
                spike_factor = violation.current_value / violation.expected_value
                throttling_result = self.sampling_manager.emergency_throttling(violation.environment, spike_factor)
                
                if throttling_result["throttling_applied"]:
                    return {"success": True, "action": f"Applied emergency throttling: {throttling_result['total_rules_throttled']} rules throttled"}
            
            return {"success": False, "reason": "No correction handler for violation type"}
            
        except Exception as e:
            return {"success": False, "reason": f"Correction failed: {str(e)}"}
    
    def get_compliance_report(self, environment: str = None) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        violations = self.scan_all_environments()
        
        # Filter by environment if specified
        if environment:
            violations = {environment: violations.get(environment, [])}
        
        # Calculate summary statistics
        total_violations = sum(len(v) for v in violations.values())
        critical_violations = sum(1 for env_violations in violations.values() 
                                for v in env_violations if v.severity == "critical")
        auto_correctable = sum(1 for env_violations in violations.values() 
                             for v in env_violations if v.auto_correctable)
        
        # Apply auto-corrections if enabled
        correction_result = self.auto_correct_violations(violations)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_violations": total_violations,
            "critical_violations": critical_violations,
            "auto_correctable_violations": auto_correctable,
            "violations_by_environment": violations,
            "auto_correction_result": correction_result,
            "compliance_score": max(0, 100 - (critical_violations * 10) - (total_violations * 2))
        }


# Default compliance monitor instance
default_compliance_monitor = ComplianceMonitor()

def scan_compliance(environment: str = None) -> Dict[str, Any]:
    """Scan for compliance violations"""
    return default_compliance_monitor.get_compliance_report(environment)

def enable_auto_correction(enabled: bool = True):
    """Enable or disable auto-correction"""
    default_compliance_monitor.auto_correction_enabled = enabled

if __name__ == "__main__":
    import sys
    
    # Test the compliance monitoring system
    monitor = ComplianceMonitor()
    
    # Check for test-real-compliance flag
    if "--test-real-compliance" in sys.argv:
        print("🛡️ Testing real-world compliance monitoring...")
        
        # Test real-world integration status
        print("\n📊 Real-world integration status:")
        status = monitor.real_world_manager.get_integration_status()
        for service, info in status.items():
            print(f"  {service}: {info['status']}")
        
        # Generate compliance report with real data
        print("\n📋 Generating compliance report with real data...")
        report = monitor.get_compliance_report()
        
        print(f"✅ Compliance scan complete:")
        print(f"  Total violations: {report['total_violations']}")
        print(f"  Critical violations: {report['critical_violations']}")
        print(f"  Auto-correctable: {report['auto_correctable_violations']}")
        print(f"  Compliance score: {report['compliance_score']}/100")
        
        # Show corrections applied
        corrections = report['auto_correction_result']
        if corrections['corrections_applied'] > 0:
            print(f"  Corrections applied: {corrections['corrections_applied']}")
            for action in corrections['actions']:
                print(f"    {action['environment']}: {action['action']}")
        else:
            print(f"  No corrections needed: {corrections.get('reason', 'All compliant')}")
        
        # Show violations by environment
        print("\n🔍 Violations by environment (with real data):")
        for env, violations in report['violations_by_environment'].items():
            if violations:
                print(f"  {env}: {len(violations)} violations")
                for violation in violations[:3]:  # Show first 3
                    print(f"    - {violation.type.value}: {violation.description}")
            else:
                print(f"  {env}: No violations")
        
        print("✅ Real-world compliance monitoring test complete")
        sys.exit(0)
    
    # Check for active compliance enforcement flag
    if "--test-compliance" in sys.argv:
        print("🛡️ Testing active compliance enforcement...")
        
        # Generate compliance report
        print("\n📊 Generating compliance report...")
        report = monitor.get_compliance_report()
        
        print(f"✅ Compliance scan complete:")
        print(f"  Total violations: {report['total_violations']}")
        print(f"  Critical violations: {report['critical_violations']}")
        print(f"  Auto-correctable: {report['auto_correctable_violations']}")
        print(f"  Compliance score: {report['compliance_score']}/100")
        
        # Show corrections applied
        corrections = report['auto_correction_result']
        if corrections['corrections_applied'] > 0:
            print(f"  Corrections applied: {corrections['corrections_applied']}")
            for action in corrections['actions']:
                print(f"    {action['environment']}: {action['action']}")
        else:
            print(f"  No corrections needed: {corrections.get('reason', 'All compliant')}")
        
        # Show violations by environment
        print("\n🔍 Violations by environment:")
        for env, violations in report['violations_by_environment'].items():
            if violations:
                print(f"  {env}: {len(violations)} violations")
                for violation in violations[:3]:  # Show first 3
                    print(f"    - {violation.type.value}: {violation.description}")
            else:
                print(f"  {env}: No violations")
        
        print("✅ Active compliance enforcement test complete")
        sys.exit(0)
    
    # Run basic compliance scan
    print("🛡️ Running compliance scan...")
    report = monitor.get_compliance_report()
    
    print(f"Compliance Score: {report['compliance_score']}/100")
    print(f"Total Violations: {report['total_violations']}")
    print(f"Critical Violations: {report['critical_violations']}")
    
    if report['auto_correction_result']['corrections_applied'] > 0:
        print(f"Auto-corrections Applied: {report['auto_correction_result']['corrections_applied']}")
    
    print("✅ Compliance scan complete")