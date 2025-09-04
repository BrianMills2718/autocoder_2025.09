#!/usr/bin/env python3
"""
Observability Sampling Policy Management

Implements default sampling policies for logs and metrics to control
observability costs while maintaining system visibility.
"""

import json
import os
import logging
from enum import Enum
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
import hashlib
import time
from datetime import datetime, timedelta

class SamplingLevel(Enum):
    """Sampling levels for different log and metric types"""
    NONE = "none"           # No sampling (0%)
    MINIMAL = "minimal"     # 1% sampling
    LOW = "low"             # 5% sampling
    MEDIUM = "medium"       # 10% sampling
    HIGH = "high"           # 25% sampling
    FULL = "full"           # 100% sampling (no sampling)

class ObservabilityType(Enum):
    """Types of observability data"""
    TRACE = "trace"
    LOG = "log"
    METRIC = "metric"
    ERROR = "error"
    PERFORMANCE = "performance"
    SECURITY = "security"
    AUDIT = "audit"

@dataclass
class SamplingRule:
    """Individual sampling rule configuration"""
    name: str
    type: ObservabilityType
    level: SamplingLevel
    rate: float  # 0.0 to 1.0
    conditions: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # Higher priority rules override lower priority
    enabled: bool = True
    
    def __post_init__(self):
        """Validate sampling rule configuration"""
        if not 0.0 <= self.rate <= 1.0:
            raise ValueError(f"Sampling rate must be between 0.0 and 1.0, got {self.rate}")
        
        # Ensure rate matches level
        level_rates = {
            SamplingLevel.NONE: 0.0,
            SamplingLevel.MINIMAL: 0.01,
            SamplingLevel.LOW: 0.05,
            SamplingLevel.MEDIUM: 0.10,
            SamplingLevel.HIGH: 0.25,
            SamplingLevel.FULL: 1.0
        }
        
        expected_rate = level_rates[self.level]
        if abs(self.rate - expected_rate) > 0.001:  # Small tolerance for floating point
            raise ValueError(f"Sampling rate {self.rate} doesn't match level {self.level.value} (expected {expected_rate})")

@dataclass
class BudgetLimit:
    """Budget limit configuration for sampling"""
    total_cost_per_month: float
    storage_gb_per_month: float
    query_cost_per_month: float
    ingestion_cost_per_month: float
    alert_threshold: float = 0.8
    hard_limit: bool = False

@dataclass
class SamplingPolicy:
    """Complete sampling policy configuration"""
    name: str
    environment: str
    rules: List[SamplingRule] = field(default_factory=list)
    global_rate_limit: Optional[int] = None  # Max events per second
    budget_limit_mb: Optional[float] = None  # Max MB per hour (deprecated)
    budget_limit: Optional[BudgetLimit] = None  # Budget limits
    created_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0"
    
    def add_rule(self, rule: SamplingRule):
        """Add a sampling rule to the policy"""
        self.rules.append(rule)
        # Sort by priority (higher priority first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def get_sampling_rate(self, obs_type: ObservabilityType, context: Dict[str, Any] = None) -> float:
        """Get the effective sampling rate for a given observability type and context"""
        context = context or {}
        
        # Find matching rules (highest priority first)
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            if rule.type != obs_type:
                continue
                
            # Check conditions
            if self._matches_conditions(rule.conditions, context):
                return rule.rate
        
        # Default to no sampling if no rule matches
        return 0.0
    
    def _matches_conditions(self, conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if context matches rule conditions"""
        if not conditions:
            return True
            
        for key, expected_value in conditions.items():
            if key not in context:
                return False
                
            context_value = context[key]
            
            # Handle different condition types
            if isinstance(expected_value, list):
                if context_value not in expected_value:
                    return False
            elif isinstance(expected_value, dict):
                # Handle range conditions
                if "min" in expected_value and context_value < expected_value["min"]:
                    return False
                if "max" in expected_value and context_value > expected_value["max"]:
                    return False
            else:
                if context_value != expected_value:
                    return False
        
        return True
    
    def should_sample(self, obs_type: ObservabilityType, context: Dict[str, Any] = None) -> bool:
        """Determine if an event should be sampled based on the policy"""
        rate = self.get_sampling_rate(obs_type, context)
        
        if rate == 0.0:
            return False
        if rate >= 1.0:
            return True
            
        # Use deterministic sampling based on context hash
        if context:
            # Create hash from context for deterministic sampling
            context_str = json.dumps(context, sort_keys=True)
            hash_value = hashlib.md5(context_str.encode()).hexdigest()
            # Use first 8 characters as hex number
            hash_int = int(hash_value[:8], 16)
            # Normalize to 0-1 range
            normalized = (hash_int % 1000000) / 1000000.0
            return normalized < rate
        else:
            # Fallback to time-based sampling
            return (time.time() * 1000000) % 1000000 < rate * 1000000

class SamplingPolicyManager:
    """Manages sampling policies for different environments"""
    
    def __init__(self, config_dir: str = "config/observability"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.policies: Dict[str, SamplingPolicy] = {}
        self.logger = logging.getLogger(__name__)
        
        # Real-world data integration
        from autocoder_cc.observability.real_world_integrations import RealWorldDataManager
        self.real_world_manager = RealWorldDataManager()
        
        # Load default policies
        self._create_default_policies()
    
    def _create_default_policies(self):
        """Create default sampling policies for different environments"""
        
        # Development Environment - High sampling for debugging
        dev_policy = SamplingPolicy(
            name="development",
            environment="development",
            global_rate_limit=1000,  # 1000 events/sec
            budget_limit_mb=100.0,   # 100 MB/hour (deprecated)
            budget_limit=BudgetLimit(
                total_cost_per_month=20.0,
                storage_gb_per_month=10.0,
                query_cost_per_month=5.0,
                ingestion_cost_per_month=2.0
            )
        )
        
        # Add development rules
        dev_rules = [
            SamplingRule("debug_logs", ObservabilityType.LOG, SamplingLevel.HIGH, 0.25, 
                        {"level": ["DEBUG", "INFO"]}, priority=10),
            SamplingRule("error_logs", ObservabilityType.ERROR, SamplingLevel.FULL, 1.0, 
                        {"level": ["ERROR", "CRITICAL"]}, priority=20),
            SamplingRule("performance_metrics", ObservabilityType.PERFORMANCE, SamplingLevel.MEDIUM, 0.10, 
                        {}, priority=5),
            SamplingRule("security_events", ObservabilityType.SECURITY, SamplingLevel.FULL, 1.0, 
                        {}, priority=25),
            SamplingRule("audit_logs", ObservabilityType.AUDIT, SamplingLevel.FULL, 1.0, 
                        {}, priority=30),
            SamplingRule("traces", ObservabilityType.TRACE, SamplingLevel.MEDIUM, 0.10, 
                        {}, priority=5)
        ]
        
        for rule in dev_rules:
            dev_policy.add_rule(rule)
        
        # Staging Environment - Moderate sampling
        staging_policy = SamplingPolicy(
            name="staging",
            environment="staging",
            global_rate_limit=500,   # 500 events/sec
            budget_limit_mb=50.0,    # 50 MB/hour (deprecated)
            budget_limit=BudgetLimit(
                total_cost_per_month=100.0,
                storage_gb_per_month=50.0,
                query_cost_per_month=15.0,
                ingestion_cost_per_month=8.0
            )
        )
        
        staging_rules = [
            SamplingRule("info_logs", ObservabilityType.LOG, SamplingLevel.LOW, 0.05, 
                        {"level": ["INFO", "DEBUG"]}, priority=10),
            SamplingRule("error_logs", ObservabilityType.ERROR, SamplingLevel.FULL, 1.0, 
                        {"level": ["ERROR", "CRITICAL"]}, priority=20),
            SamplingRule("performance_metrics", ObservabilityType.PERFORMANCE, SamplingLevel.LOW, 0.05, 
                        {}, priority=5),
            SamplingRule("security_events", ObservabilityType.SECURITY, SamplingLevel.FULL, 1.0, 
                        {}, priority=25),
            SamplingRule("audit_logs", ObservabilityType.AUDIT, SamplingLevel.FULL, 1.0, 
                        {}, priority=30),
            SamplingRule("traces", ObservabilityType.TRACE, SamplingLevel.LOW, 0.05, 
                        {}, priority=5)
        ]
        
        for rule in staging_rules:
            staging_policy.add_rule(rule)
        
        # Production Environment - Minimal sampling for cost control
        prod_policy = SamplingPolicy(
            name="production",
            environment="production",
            global_rate_limit=200,   # 200 events/sec
            budget_limit_mb=25.0,    # 25 MB/hour (deprecated)
            budget_limit=BudgetLimit(
                total_cost_per_month=500.0,
                storage_gb_per_month=200.0,
                query_cost_per_month=50.0,
                ingestion_cost_per_month=25.0,
                hard_limit=True  # Enable hard limit enforcement for production
            )
        )
        
        prod_rules = [
            SamplingRule("info_logs", ObservabilityType.LOG, SamplingLevel.MINIMAL, 0.01, 
                        {"level": ["INFO", "DEBUG"]}, priority=10),
            SamplingRule("warn_logs", ObservabilityType.LOG, SamplingLevel.LOW, 0.05, 
                        {"level": ["WARNING"]}, priority=15),
            SamplingRule("error_logs", ObservabilityType.ERROR, SamplingLevel.FULL, 1.0, 
                        {"level": ["ERROR", "CRITICAL"]}, priority=20),
            SamplingRule("performance_metrics", ObservabilityType.PERFORMANCE, SamplingLevel.MINIMAL, 0.01, 
                        {}, priority=5),
            SamplingRule("security_events", ObservabilityType.SECURITY, SamplingLevel.FULL, 1.0, 
                        {}, priority=25),
            SamplingRule("audit_logs", ObservabilityType.AUDIT, SamplingLevel.FULL, 1.0, 
                        {}, priority=30),
            SamplingRule("traces", ObservabilityType.TRACE, SamplingLevel.MINIMAL, 0.01, 
                        {}, priority=5)
        ]
        
        for rule in prod_rules:
            prod_policy.add_rule(rule)
        
        # Store policies
        self.policies["development"] = dev_policy
        self.policies["staging"] = staging_policy
        self.policies["production"] = prod_policy
    
    def get_policy(self, environment: str) -> Optional[SamplingPolicy]:
        """Get sampling policy for environment"""
        return self.policies.get(environment)
    
    def save_policy(self, policy: SamplingPolicy, filename: Optional[str] = None):
        """Save sampling policy to file"""
        if filename is None:
            filename = f"sampling_policy_{policy.environment}.json"
        
        filepath = self.config_dir / filename
        
        # Convert to dict for JSON serialization
        policy_dict = asdict(policy)
        
        # Handle datetime and enum serialization
        policy_dict["created_at"] = policy.created_at.isoformat()
        for rule in policy_dict["rules"]:
            rule["type"] = rule["type"].value
            rule["level"] = rule["level"].value
        
        with open(filepath, 'w') as f:
            json.dump(policy_dict, f, indent=2)
        
        self.logger.info(f"Saved sampling policy for {policy.environment} to {filepath}")
    
    def load_policy(self, filename: str) -> SamplingPolicy:
        """Load sampling policy from file"""
        filepath = self.config_dir / filename
        
        with open(filepath, 'r') as f:
            policy_dict = json.load(f)
        
        # Handle datetime and enum deserialization
        policy_dict["created_at"] = datetime.fromisoformat(policy_dict["created_at"])
        
        rules = []
        for rule_dict in policy_dict["rules"]:
            rule_dict["type"] = ObservabilityType(rule_dict["type"])
            rule_dict["level"] = SamplingLevel(rule_dict["level"])
            rules.append(SamplingRule(**rule_dict))
        
        policy_dict["rules"] = rules
        
        policy = SamplingPolicy(**policy_dict)
        self.policies[policy.environment] = policy
        
        self.logger.info(f"Loaded sampling policy for {policy.environment} from {filepath}")
        return policy
    
    def validate_budgets(self, environment: str = None) -> Dict[str, Any]:
        """Validate sampling policies and budget configurations"""
        results = {
            "valid": True,
            "policies": {},
            "total_policies": 0,
            "errors": []
        }
        
        policies_to_check = [environment] if environment else self.policies.keys()
        
        for env in policies_to_check:
            policy = self.policies.get(env)
            if not policy:
                results["errors"].append(f"Policy not found for environment: {env}")
                results["valid"] = False
                continue
            
            policy_result = {
                "environment": env,
                "rules": len(policy.rules),
                "budget_limit_mb": policy.budget_limit_mb,
                "rate_limit": policy.global_rate_limit,
                "estimated_cost": self._estimate_cost(policy),
                "valid": True,
                "warnings": []
            }
            
            # Validate rules
            for rule in policy.rules:
                try:
                    # Rule validation happens in __post_init__
                    pass
                except ValueError as e:
                    policy_result["valid"] = False
                    policy_result["warnings"].append(f"Rule {rule.name}: {e}")
            
            # Check budget reasonableness
            if policy.budget_limit_mb and policy.budget_limit_mb > 1000:
                policy_result["warnings"].append(f"High budget limit: {policy.budget_limit_mb} MB/hour")
            
            if policy.global_rate_limit and policy.global_rate_limit > 10000:
                policy_result["warnings"].append(f"High rate limit: {policy.global_rate_limit} events/sec")
            
            results["policies"][env] = policy_result
            results["total_policies"] += 1
            
            if not policy_result["valid"]:
                results["valid"] = False
        
        return results
    
    def enforce_budget_limits(self, environment: str, current_costs: Dict[str, float]) -> Dict[str, Any]:
        """Enforce hard budget limits with automatic sampling rate reduction"""
        policy = self.get_policy(environment)
        if not policy or not policy.budget_limit:
            return {"enforcement_applied": False, "reason": "No budget limit set"}
        
        budget = policy.budget_limit
        total_current_cost = sum(current_costs.values())
        
        # Check if hard limit enforcement is enabled
        if not budget.hard_limit:
            return {"enforcement_applied": False, "reason": "Hard limit enforcement disabled"}
        
        # Check if budget is exceeded
        if total_current_cost <= budget.total_cost_per_month:
            return {"enforcement_applied": False, "reason": "Budget not exceeded"}
        
        # Calculate required cost reduction
        overage = total_current_cost - budget.total_cost_per_month
        reduction_factor = 1.0 - (budget.total_cost_per_month / total_current_cost)
        
        # Apply sampling rate reduction to non-critical data types
        enforcement_actions = []
        
        for rule in policy.rules:
            # Never reduce sampling for critical data types
            if rule.type in [ObservabilityType.ERROR, ObservabilityType.SECURITY, ObservabilityType.AUDIT]:
                continue
            
            # Only reduce sampling for enabled rules with rates > 0
            if rule.enabled and rule.rate > 0:
                original_rate = rule.rate
                new_rate = max(0.001, rule.rate * (1.0 - reduction_factor))  # Minimum 0.1% sampling
                
                if new_rate != original_rate:
                    rule.rate = new_rate
                    enforcement_actions.append({
                        "rule": rule.name,
                        "obs_type": rule.type.value,
                        "original_rate": original_rate,
                        "new_rate": new_rate,
                        "reduction_percent": (original_rate - new_rate) / original_rate * 100
                    })
        
        self.logger.warning(f"Budget enforcement applied to {environment}: ${overage:.2f} overage, {len(enforcement_actions)} rules modified")
        
        return {
            "enforcement_applied": True,
            "budget_overage": overage,
            "reduction_factor": reduction_factor,
            "actions": enforcement_actions,
            "total_rules_modified": len(enforcement_actions)
        }
    
    def emergency_throttling(self, environment: str, cost_spike_factor: float) -> Dict[str, Any]:
        """Implement emergency throttling for cost spikes"""
        policy = self.get_policy(environment)
        if not policy:
            return {"throttling_applied": False, "reason": "Policy not found"}
        
        # Emergency throttling triggers when costs spike by specified factor
        if cost_spike_factor < 2.0:
            return {"throttling_applied": False, "reason": "Cost spike factor too low for emergency throttling"}
        
        # Calculate throttling factor based on spike severity
        throttling_factor = min(0.9, 1.0 - (1.0 / cost_spike_factor))  # Max 90% reduction
        
        # Apply emergency throttling to all non-critical data types
        throttling_actions = []
        
        for rule in policy.rules:
            # Never throttle critical data types
            if rule.type in [ObservabilityType.ERROR, ObservabilityType.SECURITY, ObservabilityType.AUDIT]:
                continue
            
            # Apply throttling to enabled rules
            if rule.enabled and rule.rate > 0:
                original_rate = rule.rate
                new_rate = max(0.001, rule.rate * (1.0 - throttling_factor))  # Minimum 0.1% sampling
                
                if new_rate != original_rate:
                    rule.rate = new_rate
                    throttling_actions.append({
                        "rule": rule.name,
                        "obs_type": rule.type.value,
                        "original_rate": original_rate,
                        "new_rate": new_rate,
                        "throttling_percent": (original_rate - new_rate) / original_rate * 100
                    })
        
        self.logger.critical(f"Emergency throttling applied to {environment}: {cost_spike_factor:.1f}x cost spike, {len(throttling_actions)} rules throttled")
        
        return {
            "throttling_applied": True,
            "cost_spike_factor": cost_spike_factor,
            "throttling_factor": throttling_factor,
            "actions": throttling_actions,
            "total_rules_throttled": len(throttling_actions)
        }

    def _estimate_cost(self, policy: SamplingPolicy) -> Dict[str, float]:
        """Estimate observability costs using real-world data"""
        # Get real cost data from APIs
        cost_data = self.real_world_manager.get_real_costs(policy.environment, days=7)
        
        # Get real data volumes
        volume_data = self.real_world_manager.get_real_data_volumes(policy.environment, hours=24)
        real_volumes = volume_data["volumes"]
        
        total_cost = 0.0
        cost_breakdown = {}
        
        # Calculate costs using real data
        for obs_type in ObservabilityType:
            rate = policy.get_sampling_rate(obs_type)
            
            # Get real volume for this data type (GB/day)
            volume_gb = real_volumes.get(obs_type.value, 0.0)
            
            # Calculate cost based on real API data and sampling rate
            if obs_type.value in ["log", "error"]:
                # Use storage cost for log-based data
                daily_cost = volume_gb * rate * (cost_data.storage_cost / (cost_data.total_cost or 1))
            elif obs_type.value in ["metric", "performance"]:
                # Use query cost for metric-based data
                daily_cost = volume_gb * rate * (cost_data.query_cost / (cost_data.total_cost or 1))
            elif obs_type.value in ["trace"]:
                # Use ingestion cost for trace data
                daily_cost = volume_gb * rate * (cost_data.ingestion_cost / (cost_data.total_cost or 1))
            elif obs_type.value in ["security", "audit"]:
                # Use full cost for critical data (compliance requirement)
                daily_cost = volume_gb * rate * (cost_data.total_cost / 7)  # 7 days of data
            else:
                # Fallback to proportional cost
                daily_cost = volume_gb * rate * (cost_data.total_cost / 7)
            
            cost_breakdown[obs_type.value] = daily_cost
            total_cost += daily_cost
        
        return {
            "total_per_hour": total_cost / 24,
            "total_per_day": total_cost,
            "total_per_month": total_cost * 30,
            "breakdown": cost_breakdown,
            "data_source": cost_data.source,
            "confidence": cost_data.confidence,
            "period": cost_data.period
        }

# Default sampling policy manager instance
default_policy_manager = SamplingPolicyManager()

def get_sampling_policy(environment: str) -> Optional[SamplingPolicy]:
    """Get sampling policy for environment"""
    return default_policy_manager.get_policy(environment)

def should_sample(obs_type: ObservabilityType, environment: str, context: Dict[str, Any] = None) -> bool:
    """Determine if an event should be sampled"""
    policy = get_sampling_policy(environment)
    if not policy:
        return False
    
    return policy.should_sample(obs_type, context)

def get_sampling_rate(obs_type: ObservabilityType, environment: str, context: Dict[str, Any] = None) -> float:
    """Get sampling rate for observability type in environment"""
    policy = get_sampling_policy(environment)
    if not policy:
        return 0.0
    
    return policy.get_sampling_rate(obs_type, context)

if __name__ == "__main__":
    import sys
    
    # Test the sampling policy system
    manager = SamplingPolicyManager()
    
    # Check for test-real-data flag
    if "--test-real-data" in sys.argv:
        print("🌍 Testing real-world data integration...")
        
        # Test real data integration
        print("\n💰 Testing real cost estimation...")
        for env in ["development", "staging", "production"]:
            policy = manager.get_policy(env)
            if policy:
                cost_estimate = manager._estimate_cost(policy)
                print(f"✅ {env}: ${cost_estimate['total_per_month']:.2f}/month")
                print(f"  Data source: {cost_estimate['data_source']}")
                print(f"  Confidence: {cost_estimate['confidence']:.1%}")
                print(f"  Period: {cost_estimate['period']}")
        
        # Test real-world integration status
        print("\n📊 Real-world integration status:")
        status = manager.real_world_manager.get_integration_status()
        for service, info in status.items():
            print(f"  {service}: {info['status']}")
        
        print("✅ Real-world data integration test complete")
        sys.exit(0)
    
    # Check for test-enforcement flag
    if "--test-enforcement" in sys.argv:
        print("🔒 Testing budget enforcement mechanisms...")
        
        # Test hard budget enforcement
        print("\n🚨 Testing hard budget enforcement...")
        # Use real cost data from API integration
        real_costs = manager.real_world_manager.get_real_cost_data("production", days=7)
        # Multiply by factor to simulate budget overage
        test_costs = {
            "sampling": real_costs.get("total_cost", 400.0) * 1.5,  # 50% over budget
            "query": real_costs.get("query_cost", 50.0), 
            "ingestion": real_costs.get("ingestion_cost", 30.0)
        }
        enforcement_result = manager.enforce_budget_limits("production", test_costs)
        
        if enforcement_result["enforcement_applied"]:
            print(f"✅ Hard budget enforcement working: ${enforcement_result['budget_overage']:.2f} overage")
            print(f"  Reduction factor: {enforcement_result['reduction_factor']:.2%}")
            print(f"  Rules modified: {enforcement_result['total_rules_modified']}")
            for action in enforcement_result["actions"]:
                print(f"    {action['rule']}: {action['original_rate']:.2%} → {action['new_rate']:.2%} ({action['reduction_percent']:.1f}% reduction)")
        else:
            print(f"❌ Hard budget enforcement failed: {enforcement_result['reason']}")
        
        # Test emergency throttling
        print("\n⚡ Testing emergency throttling...")
        throttling_result = manager.emergency_throttling("production", 5.0)  # 5x cost spike
        
        if throttling_result["throttling_applied"]:
            print(f"✅ Emergency throttling working: {throttling_result['cost_spike_factor']:.1f}x spike")
            print(f"  Throttling factor: {throttling_result['throttling_factor']:.2%}")
            print(f"  Rules throttled: {throttling_result['total_rules_throttled']}")
            for action in throttling_result["actions"]:
                print(f"    {action['rule']}: {action['original_rate']:.2%} → {action['new_rate']:.2%} ({action['throttling_percent']:.1f}% throttling)")
        else:
            print(f"❌ Emergency throttling failed: {throttling_result['reason']}")
        
        print("✅ Budget enforcement test complete")
        sys.exit(0)
    
    # Test validation
    print("🔍 Validating sampling policies...")
    results = manager.validate_budgets()
    
    if results["valid"]:
        print("✅ All sampling policies valid")
        for env, policy_result in results["policies"].items():
            policy = manager.get_policy(env)
            target_budget = policy.budget_limit.total_cost_per_month if policy.budget_limit else "None"
            estimated_cost = policy_result["estimated_cost"]["total_per_month"]
            print(f"  {env}: {policy_result['rules']} rules, target: ${target_budget}/month, estimated: ${estimated_cost:.2f}/month")
    else:
        print("❌ Validation errors found:")
        for error in results["errors"]:
            print(f"  - {error}")
    
    # Test sampling decisions
    print("\n🎲 Testing sampling decisions...")
    test_cases = [
        (ObservabilityType.LOG, "development", {"level": "DEBUG"}),
        (ObservabilityType.LOG, "production", {"level": "DEBUG"}),
        (ObservabilityType.ERROR, "production", {"level": "ERROR"}),
        (ObservabilityType.SECURITY, "production", {}),
        (ObservabilityType.PERFORMANCE, "development", {}),
    ]
    
    for obs_type, env, context in test_cases:
        rate = get_sampling_rate(obs_type, env, context)
        should_sample_result = should_sample(obs_type, env, context)
        print(f"  {obs_type.value} in {env}: rate={rate:.2%}, sample={should_sample_result}")
    
    # Save policies
    print("\n💾 Saving policies...")
    for env, policy in manager.policies.items():
        manager.save_policy(policy)
    
    print("✅ Sampling policy system test complete")