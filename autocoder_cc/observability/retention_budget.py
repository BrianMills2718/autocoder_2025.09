#!/usr/bin/env python3
"""
Observability Retention Budget Management

Manages retention policies and budget enforcement for observability data
to control long-term storage costs while maintaining compliance requirements.
"""

import json
import logging
from enum import Enum
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
import math

class RetentionPeriod(Enum):
    """Standard retention periods"""
    HOURS_1 = "1h"
    HOURS_6 = "6h"
    HOURS_12 = "12h"
    DAYS_1 = "1d"
    DAYS_7 = "7d"
    DAYS_30 = "30d"
    DAYS_90 = "90d"
    DAYS_365 = "365d"
    YEARS_7 = "7y"
    PERMANENT = "permanent"

class StorageTier(Enum):
    """Storage tiers with different cost profiles"""
    HOT = "hot"           # Immediate access, highest cost
    WARM = "warm"         # Quick access, medium cost
    COLD = "cold"         # Slower access, low cost
    ARCHIVE = "archive"   # Rare access, lowest cost

@dataclass
class RetentionRule:
    """Individual retention rule configuration"""
    name: str
    obs_type: str  # ObservabilityType as string to avoid circular imports
    retention_period: RetentionPeriod
    storage_tier: StorageTier
    conditions: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    enabled: bool = True
    compliance_required: bool = False
    
    def get_retention_days(self) -> int:
        """Convert retention period to days"""
        period_map = {
            RetentionPeriod.HOURS_1: 1/24,
            RetentionPeriod.HOURS_6: 6/24,
            RetentionPeriod.HOURS_12: 12/24,
            RetentionPeriod.DAYS_1: 1,
            RetentionPeriod.DAYS_7: 7,
            RetentionPeriod.DAYS_30: 30,
            RetentionPeriod.DAYS_90: 90,
            RetentionPeriod.DAYS_365: 365,
            RetentionPeriod.YEARS_7: 365 * 7,
            RetentionPeriod.PERMANENT: float('inf')
        }
        return period_map[self.retention_period]

@dataclass
class BudgetLimit:
    """Budget limit configuration"""
    storage_gb_per_month: float
    query_cost_per_month: float
    ingestion_cost_per_month: float
    total_cost_per_month: float
    alert_threshold: float = 0.8  # Alert at 80% of budget
    hard_limit: bool = False      # Whether to enforce hard limits

@dataclass
class RetentionPolicy:
    """Complete retention policy configuration"""
    name: str
    environment: str
    rules: List[RetentionRule] = field(default_factory=list)
    budget_limit: Optional[BudgetLimit] = None
    default_retention: RetentionPeriod = RetentionPeriod.DAYS_7
    default_storage_tier: StorageTier = StorageTier.WARM
    created_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0"
    
    def add_rule(self, rule: RetentionRule):
        """Add a retention rule to the policy"""
        self.rules.append(rule)
        # Sort by priority (higher priority first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def get_retention_config(self, obs_type: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get retention configuration for observability type and context"""
        context = context or {}
        
        # Find matching rule (highest priority first)
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            if rule.obs_type != obs_type:
                continue
                
            # Check conditions
            if self._matches_conditions(rule.conditions, context):
                return {
                    "retention_period": rule.retention_period.value,
                    "retention_days": rule.get_retention_days(),
                    "storage_tier": rule.storage_tier.value,
                    "compliance_required": rule.compliance_required,
                    "rule_name": rule.name
                }
        
        # Return default configuration
        return {
            "retention_period": self.default_retention.value,
            "retention_days": self._get_default_retention_days(),
            "storage_tier": self.default_storage_tier.value,
            "compliance_required": False,
            "rule_name": "default"
        }
    
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
    
    def _get_default_retention_days(self) -> int:
        """Get default retention in days"""
        period_map = {
            RetentionPeriod.HOURS_1: 1/24,
            RetentionPeriod.HOURS_6: 6/24,
            RetentionPeriod.HOURS_12: 12/24,
            RetentionPeriod.DAYS_1: 1,
            RetentionPeriod.DAYS_7: 7,
            RetentionPeriod.DAYS_30: 30,
            RetentionPeriod.DAYS_90: 90,
            RetentionPeriod.DAYS_365: 365,
            RetentionPeriod.YEARS_7: 365 * 7,
            RetentionPeriod.PERMANENT: float('inf')
        }
        return period_map[self.default_retention]

class CostOptimizationEngine:
    """Unified cost optimization across sampling and retention policies"""
    
    def __init__(self, retention_manager=None):
        self.retention_manager = retention_manager or RetentionBudgetManager()
        self.logger = logging.getLogger(__name__)
    
    def unified_optimization(self, environment: str, target_cost: float, 
                           current_sampling_cost: float, current_retention_cost: float) -> Dict[str, Any]:
        """Perform unified optimization across both sampling and retention to meet target cost"""
        total_current_cost = current_sampling_cost + current_retention_cost
        
        if total_current_cost <= target_cost:
            return {"optimization_applied": False, "reason": "Already within target cost"}
        
        cost_reduction_needed = total_current_cost - target_cost
        
        # Prioritize retention optimization first (usually higher impact)
        retention_target = max(target_cost * 0.3, current_retention_cost - (cost_reduction_needed * 0.7))
        retention_result = self.retention_manager.reallocate_budget(environment, retention_target)
        
        retention_savings = retention_result.get("estimated_savings", 0) if retention_result.get("reallocation_applied") else 0
        
        # Calculate remaining cost reduction needed
        remaining_reduction = cost_reduction_needed - retention_savings
        
        optimization_actions = {
            "retention_actions": retention_result.get("actions", []),
            "retention_savings": retention_savings,
            "sampling_reduction_needed": max(0, remaining_reduction)
        }
        
        self.logger.info(f"Unified optimization for {environment}: ${cost_reduction_needed:.2f} reduction needed, ${retention_savings:.2f} from retention, ${remaining_reduction:.2f} from sampling")
        
        return {
            "optimization_applied": True,
            "total_cost_reduction_needed": cost_reduction_needed,
            "retention_savings": retention_savings,
            "sampling_reduction_needed": remaining_reduction,
            "optimization_actions": optimization_actions
        }

class RetentionBudgetManager:
    """Manages retention policies and budget enforcement"""
    
    def __init__(self, config_dir: str = "config/observability"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.policies: Dict[str, RetentionPolicy] = {}
        self.logger = logging.getLogger(__name__)
        
        # Real-world data integration
        from autocoder_cc.observability.real_world_integrations import RealWorldDataManager
        self.real_world_manager = RealWorldDataManager()
        
        # Storage cost estimates per GB per month
        self.storage_costs = {
            StorageTier.HOT: 0.023,     # $0.023/GB/month (similar to S3 Standard)
            StorageTier.WARM: 0.0125,   # $0.0125/GB/month (similar to S3 Standard-IA)
            StorageTier.COLD: 0.004,    # $0.004/GB/month (similar to S3 Glacier)
            StorageTier.ARCHIVE: 0.001  # $0.001/GB/month (similar to S3 Deep Archive)
        }
        
        # Create default policies
        self._create_default_policies()
    
    def _create_default_policies(self):
        """Create default retention policies for different environments"""
        
        # Development Environment - Short retention, cost-focused
        dev_policy = RetentionPolicy(
            name="development",
            environment="development",
            default_retention=RetentionPeriod.DAYS_1,
            default_storage_tier=StorageTier.HOT,
            budget_limit=BudgetLimit(
                storage_gb_per_month=10.0,
                query_cost_per_month=5.0,
                ingestion_cost_per_month=2.0,
                total_cost_per_month=20.0
            )
        )
        
        # Development retention rules
        dev_rules = [
            RetentionRule("debug_logs", "log", RetentionPeriod.HOURS_12, StorageTier.HOT,
                         {"level": ["DEBUG"]}, priority=10),
            RetentionRule("info_logs", "log", RetentionPeriod.DAYS_1, StorageTier.HOT,
                         {"level": ["INFO"]}, priority=15),
            RetentionRule("error_logs", "error", RetentionPeriod.DAYS_7, StorageTier.HOT,
                         {"level": ["ERROR", "CRITICAL"]}, priority=20),
            RetentionRule("performance_metrics", "performance", RetentionPeriod.DAYS_1, StorageTier.HOT,
                         {}, priority=5),
            RetentionRule("security_events", "security", RetentionPeriod.DAYS_30, StorageTier.WARM,
                         {}, priority=25, compliance_required=True),
            RetentionRule("audit_logs", "audit", RetentionPeriod.DAYS_30, StorageTier.WARM,
                         {}, priority=30, compliance_required=True),
            RetentionRule("traces", "trace", RetentionPeriod.HOURS_6, StorageTier.HOT,
                         {}, priority=5)
        ]
        
        for rule in dev_rules:
            dev_policy.add_rule(rule)
        
        # Staging Environment - Medium retention
        staging_policy = RetentionPolicy(
            name="staging",
            environment="staging",
            default_retention=RetentionPeriod.DAYS_7,
            default_storage_tier=StorageTier.WARM,
            budget_limit=BudgetLimit(
                storage_gb_per_month=50.0,
                query_cost_per_month=15.0,
                ingestion_cost_per_month=8.0,
                total_cost_per_month=100.0
            )
        )
        
        staging_rules = [
            RetentionRule("debug_logs", "log", RetentionPeriod.DAYS_1, StorageTier.WARM,
                         {"level": ["DEBUG"]}, priority=10),
            RetentionRule("info_logs", "log", RetentionPeriod.DAYS_7, StorageTier.WARM,
                         {"level": ["INFO"]}, priority=15),
            RetentionRule("error_logs", "error", RetentionPeriod.DAYS_30, StorageTier.WARM,
                         {"level": ["ERROR", "CRITICAL"]}, priority=20),
            RetentionRule("performance_metrics", "performance", RetentionPeriod.DAYS_7, StorageTier.WARM,
                         {}, priority=5),
            RetentionRule("security_events", "security", RetentionPeriod.DAYS_90, StorageTier.COLD,
                         {}, priority=25, compliance_required=True),
            RetentionRule("audit_logs", "audit", RetentionPeriod.DAYS_90, StorageTier.COLD,
                         {}, priority=30, compliance_required=True),
            RetentionRule("traces", "trace", RetentionPeriod.DAYS_1, StorageTier.WARM,
                         {}, priority=5)
        ]
        
        for rule in staging_rules:
            staging_policy.add_rule(rule)
        
        # Production Environment - Long retention for compliance
        prod_policy = RetentionPolicy(
            name="production",
            environment="production",
            default_retention=RetentionPeriod.DAYS_30,
            default_storage_tier=StorageTier.COLD,
            budget_limit=BudgetLimit(
                storage_gb_per_month=200.0,
                query_cost_per_month=50.0,
                ingestion_cost_per_month=25.0,
                total_cost_per_month=500.0
            )
        )
        
        prod_rules = [
            RetentionRule("debug_logs", "log", RetentionPeriod.DAYS_7, StorageTier.COLD,
                         {"level": ["DEBUG"]}, priority=10),
            RetentionRule("info_logs", "log", RetentionPeriod.DAYS_30, StorageTier.COLD,
                         {"level": ["INFO"]}, priority=15),
            RetentionRule("error_logs", "error", RetentionPeriod.DAYS_365, StorageTier.WARM,
                         {"level": ["ERROR", "CRITICAL"]}, priority=20, compliance_required=True),
            RetentionRule("performance_metrics", "performance", RetentionPeriod.DAYS_90, StorageTier.COLD,
                         {}, priority=5),
            RetentionRule("security_events", "security", RetentionPeriod.YEARS_7, StorageTier.ARCHIVE,
                         {}, priority=25, compliance_required=True),
            RetentionRule("audit_logs", "audit", RetentionPeriod.YEARS_7, StorageTier.ARCHIVE,
                         {}, priority=30, compliance_required=True),
            RetentionRule("traces", "trace", RetentionPeriod.DAYS_7, StorageTier.COLD,
                         {}, priority=5)
        ]
        
        for rule in prod_rules:
            prod_policy.add_rule(rule)
        
        # Store policies
        self.policies["development"] = dev_policy
        self.policies["staging"] = staging_policy
        self.policies["production"] = prod_policy
    
    def get_policy(self, environment: str) -> Optional[RetentionPolicy]:
        """Get retention policy for environment"""
        return self.policies.get(environment)
    
    def estimate_storage_cost(self, policy: RetentionPolicy, 
                            data_volume_gb_per_day: Dict[str, float]) -> Dict[str, Any]:
        """Estimate storage costs for a retention policy"""
        total_cost = 0.0
        cost_breakdown = {}
        storage_breakdown = {}
        
        for obs_type, daily_volume in data_volume_gb_per_day.items():
            config = policy.get_retention_config(obs_type)
            retention_days = config["retention_days"]
            storage_tier = StorageTier(config["storage_tier"])
            
            # Calculate total storage (daily volume * retention days)
            total_storage_gb = daily_volume * retention_days
            
            # Calculate monthly cost
            monthly_cost = total_storage_gb * self.storage_costs[storage_tier]
            
            cost_breakdown[obs_type] = {
                "daily_volume_gb": daily_volume,
                "retention_days": retention_days,
                "total_storage_gb": total_storage_gb,
                "storage_tier": storage_tier.value,
                "monthly_cost": monthly_cost
            }
            
            storage_breakdown[storage_tier.value] = storage_breakdown.get(storage_tier.value, 0) + total_storage_gb
            total_cost += monthly_cost
        
        return {
            "total_monthly_cost": total_cost,
            "cost_breakdown": cost_breakdown,
            "storage_by_tier": storage_breakdown,
            "budget_utilization": total_cost / policy.budget_limit.total_cost_per_month if policy.budget_limit else 0
        }
    
    def check_budget_compliance(self, environment: str, 
                               actual_costs: Dict[str, float]) -> Dict[str, Any]:
        """Check if actual costs are within budget limits"""
        policy = self.get_policy(environment)
        if not policy or not policy.budget_limit:
            return {"compliant": True, "reason": "No budget limit set"}
        
        budget = policy.budget_limit
        
        # Calculate total actual cost
        total_actual = sum(actual_costs.values())
        
        # Check individual budget components
        compliance_results = {
            "compliant": True,
            "total_cost": total_actual,
            "budget_limit": budget.total_cost_per_month,
            "utilization": total_actual / budget.total_cost_per_month,
            "alert_threshold": budget.alert_threshold,
            "hard_limit": budget.hard_limit,
            "violations": []
        }
        
        # Check total budget
        if total_actual > budget.total_cost_per_month:
            compliance_results["compliant"] = False
            compliance_results["violations"].append({
                "type": "total_budget_exceeded",
                "actual": total_actual,
                "limit": budget.total_cost_per_month,
                "overage": total_actual - budget.total_cost_per_month
            })
        
        # Check alert threshold
        if total_actual > budget.total_cost_per_month * budget.alert_threshold:
            compliance_results["violations"].append({
                "type": "alert_threshold_exceeded",
                "actual": total_actual,
                "threshold": budget.total_cost_per_month * budget.alert_threshold,
                "utilization": total_actual / budget.total_cost_per_month
            })
        
        # Check component budgets
        component_checks = [
            ("storage", "storage_gb_per_month"),
            ("query", "query_cost_per_month"),
            ("ingestion", "ingestion_cost_per_month")
        ]
        
        for component, budget_attr in component_checks:
            if component in actual_costs:
                actual_component = actual_costs[component]
                budget_component = getattr(budget, budget_attr)
                
                if actual_component > budget_component:
                    compliance_results["compliant"] = False
                    compliance_results["violations"].append({
                        "type": f"{component}_budget_exceeded",
                        "actual": actual_component,
                        "limit": budget_component,
                        "overage": actual_component - budget_component
                    })
        
        return compliance_results
    
    def optimize_retention(self, environment: str, 
                          current_costs: Dict[str, float],
                          target_cost: float) -> Dict[str, Any]:
        """Suggest retention policy optimizations to meet target cost"""
        policy = self.get_policy(environment)
        if not policy:
            return {"error": "Policy not found"}
        
        current_total = sum(current_costs.values())
        if current_total <= target_cost:
            return {"optimized": False, "reason": "Already within target cost"}
        
        # Calculate required cost reduction
        cost_reduction_needed = current_total - target_cost
        reduction_percentage = cost_reduction_needed / current_total
        
        suggestions = []
        
        # Suggest moving to cheaper storage tiers
        for rule in policy.rules:
            if rule.storage_tier == StorageTier.HOT:
                savings = current_costs.get(rule.obs_type, 0) * 0.5  # Estimate 50% savings
                suggestions.append({
                    "type": "storage_tier_change",
                    "rule": rule.name,
                    "obs_type": rule.obs_type,
                    "current_tier": rule.storage_tier.value,
                    "suggested_tier": StorageTier.WARM.value,
                    "estimated_savings": savings
                })
            elif rule.storage_tier == StorageTier.WARM:
                savings = current_costs.get(rule.obs_type, 0) * 0.3  # Estimate 30% savings
                suggestions.append({
                    "type": "storage_tier_change",
                    "rule": rule.name,
                    "obs_type": rule.obs_type,
                    "current_tier": rule.storage_tier.value,
                    "suggested_tier": StorageTier.COLD.value,
                    "estimated_savings": savings
                })
        
        # Suggest reducing retention periods
        for rule in policy.rules:
            if not rule.compliance_required:
                current_days = rule.get_retention_days()
                if current_days > 30:
                    # Suggest reducing to 30 days
                    savings = current_costs.get(rule.obs_type, 0) * 0.4  # Estimate 40% savings
                    suggestions.append({
                        "type": "retention_reduction",
                        "rule": rule.name,
                        "obs_type": rule.obs_type,
                        "current_retention": rule.retention_period.value,
                        "suggested_retention": RetentionPeriod.DAYS_30.value,
                        "estimated_savings": savings
                    })
                elif current_days > 7:
                    # Suggest reducing to 7 days
                    savings = current_costs.get(rule.obs_type, 0) * 0.25  # Estimate 25% savings
                    suggestions.append({
                        "type": "retention_reduction",
                        "rule": rule.name,
                        "obs_type": rule.obs_type,
                        "current_retention": rule.retention_period.value,
                        "suggested_retention": RetentionPeriod.DAYS_7.value,
                        "estimated_savings": savings
                    })
        
        # Sort suggestions by estimated savings (descending)
        suggestions.sort(key=lambda x: x["estimated_savings"], reverse=True)
        
        return {
            "optimized": True,
            "current_cost": current_total,
            "target_cost": target_cost,
            "cost_reduction_needed": cost_reduction_needed,
            "reduction_percentage": reduction_percentage,
            "suggestions": suggestions[:5]  # Top 5 suggestions
        }
    
    def reallocate_budget(self, environment: str, target_cost: float) -> Dict[str, Any]:
        """Reallocate budget using real-world data volumes"""
        policy = self.get_policy(environment)
        if not policy:
            return {"reallocation_applied": False, "reason": "Policy not found"}
        
        if not policy.budget_limit:
            return {"reallocation_applied": False, "reason": "No budget limit set"}
        
        # Get real data volumes from Prometheus
        volume_data = self.real_world_manager.get_real_data_volumes(environment)
        real_volumes = volume_data["volumes"]
        
        # Use real volumes for cost estimation
        current_estimate = self.estimate_storage_cost(policy, real_volumes)
        current_total = current_estimate["total_monthly_cost"]
        
        if current_total <= target_cost:
            return {"reallocation_applied": False, "reason": "Already within target cost"}
        
        # Calculate required cost reduction
        reduction_needed = current_total - target_cost
        reduction_factor = reduction_needed / current_total
        
        # Apply reallocation strategies
        reallocation_actions = []
        
        # Strategy 1: Move non-critical data to cheaper storage tiers
        for rule in policy.rules:
            if rule.compliance_required:
                continue  # Never modify compliance-required rules
            
            # Get real volume for this rule's data type
            rule_volume = real_volumes.get(rule.obs_type, 0.0)
            
            # Move hot/warm to cold/archive
            if rule.storage_tier == StorageTier.HOT:
                rule.storage_tier = StorageTier.COLD
                # Calculate actual savings based on real volume
                savings_per_gb = 0.019  # $0.023 - $0.004 = $0.019/GB/month
                estimated_savings = rule_volume * rule.get_retention_days() * savings_per_gb
                reallocation_actions.append({
                    "rule": rule.name,
                    "action": "storage_tier_change",
                    "from_tier": "hot",
                    "to_tier": "cold",
                    "estimated_savings": estimated_savings,
                    "real_volume_gb": rule_volume
                })
            elif rule.storage_tier == StorageTier.WARM:
                rule.storage_tier = StorageTier.COLD
                # Calculate actual savings based on real volume
                savings_per_gb = 0.0085  # $0.0125 - $0.004 = $0.0085/GB/month
                estimated_savings = rule_volume * rule.get_retention_days() * savings_per_gb
                reallocation_actions.append({
                    "rule": rule.name,
                    "action": "storage_tier_change",
                    "from_tier": "warm",
                    "to_tier": "cold",
                    "estimated_savings": estimated_savings,
                    "real_volume_gb": rule_volume
                })
        
        # Strategy 2: Reduce retention periods for non-critical data
        for rule in policy.rules:
            if rule.compliance_required:
                continue
            
            rule_volume = real_volumes.get(rule.obs_type, 0.0)
            current_days = rule.get_retention_days()
            
            if current_days > 30:
                rule.retention_period = RetentionPeriod.DAYS_30
                # Calculate actual savings based on real volume
                savings_days = current_days - 30
                estimated_savings = rule_volume * savings_days * self.storage_costs[rule.storage_tier]
                reallocation_actions.append({
                    "rule": rule.name,
                    "action": "retention_reduction",
                    "from_period": f"{current_days}d",
                    "to_period": "30d",
                    "estimated_savings": estimated_savings,
                    "real_volume_gb": rule_volume
                })
            elif current_days > 7:
                rule.retention_period = RetentionPeriod.DAYS_7
                # Calculate actual savings based on real volume
                savings_days = current_days - 7
                estimated_savings = rule_volume * savings_days * self.storage_costs[rule.storage_tier]
                reallocation_actions.append({
                    "rule": rule.name,
                    "action": "retention_reduction",
                    "from_period": f"{current_days}d",
                    "to_period": "7d",
                    "estimated_savings": estimated_savings,
                    "real_volume_gb": rule_volume
                })
        
        # Calculate total estimated savings
        total_savings = sum(action.get("estimated_savings", 0) for action in reallocation_actions)
        
        self.logger.info(f"Budget reallocation applied to {environment}: {len(reallocation_actions)} changes, estimated savings: ${total_savings:.2f}/month")
        
        return {
            "reallocation_applied": True,
            "target_cost": target_cost,
            "original_cost": current_total,
            "cost_reduction_needed": reduction_needed,
            "actions": reallocation_actions,
            "total_actions": len(reallocation_actions),
            "estimated_savings": total_savings,
            "real_volumes_used": real_volumes
        }
    
    def save_policy(self, policy: RetentionPolicy, filename: Optional[str] = None):
        """Save retention policy to file"""
        if filename is None:
            filename = f"retention_policy_{policy.environment}.json"
        
        filepath = self.config_dir / filename
        
        # Convert to dict for JSON serialization
        policy_dict = asdict(policy)
        
        # Handle datetime and enum serialization
        policy_dict["created_at"] = policy.created_at.isoformat()
        policy_dict["default_retention"] = policy.default_retention.value
        policy_dict["default_storage_tier"] = policy.default_storage_tier.value
        
        for rule in policy_dict["rules"]:
            rule["retention_period"] = rule["retention_period"].value
            rule["storage_tier"] = rule["storage_tier"].value
        
        with open(filepath, 'w') as f:
            json.dump(policy_dict, f, indent=2)
        
        self.logger.info(f"Saved retention policy for {policy.environment} to {filepath}")
    
    def load_policy(self, filename: str) -> RetentionPolicy:
        """Load retention policy from file"""
        filepath = self.config_dir / filename
        
        with open(filepath, 'r') as f:
            policy_dict = json.load(f)
        
        # Handle datetime and enum deserialization
        policy_dict["created_at"] = datetime.fromisoformat(policy_dict["created_at"])
        policy_dict["default_retention"] = RetentionPeriod(policy_dict["default_retention"])
        policy_dict["default_storage_tier"] = StorageTier(policy_dict["default_storage_tier"])
        
        # Handle budget limit
        if policy_dict.get("budget_limit"):
            policy_dict["budget_limit"] = BudgetLimit(**policy_dict["budget_limit"])
        
        # Handle rules
        rules = []
        for rule_dict in policy_dict["rules"]:
            rule_dict["retention_period"] = RetentionPeriod(rule_dict["retention_period"])
            rule_dict["storage_tier"] = StorageTier(rule_dict["storage_tier"])
            rules.append(RetentionRule(**rule_dict))
        
        policy_dict["rules"] = rules
        
        policy = RetentionPolicy(**policy_dict)
        self.policies[policy.environment] = policy
        
        self.logger.info(f"Loaded retention policy for {policy.environment} from {filepath}")
        return policy

# Default retention budget manager instance
default_budget_manager = RetentionBudgetManager()

def get_retention_policy(environment: str) -> Optional[RetentionPolicy]:
    """Get retention policy for environment"""
    return default_budget_manager.get_policy(environment)

def get_retention_config(obs_type: str, environment: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Get retention configuration for observability type in environment"""
    policy = get_retention_policy(environment)
    if not policy:
        return {
            "retention_period": "7d",
            "retention_days": 7,
            "storage_tier": "warm",
            "compliance_required": False,
            "rule_name": "fallback"
        }
    
    return policy.get_retention_config(obs_type, context)

if __name__ == "__main__":
    import sys
    
    # Test the retention budget system
    manager = RetentionBudgetManager()
    
    # Check for test-real-volumes flag
    if "--test-real-volumes" in sys.argv:
        print("🌍 Testing real-world volume integration...")
        
        # Test real volume integration
        print("\n📊 Testing real data volumes...")
        for env in ["development", "staging", "production"]:
            volume_data = manager.real_world_manager.get_real_data_volumes(env)
            real_volumes = volume_data["volumes"]
            print(f"✅ {env} volumes:")
            for data_type, volume in real_volumes.items():
                print(f"  {data_type}: {volume:.3f} GB/day")
            print(f"  Data source: {volume_data['data_source']}")
            print(f"  Confidence: {volume_data['confidence']:.1%}")
        
        # Test budget reallocation with real volumes
        print("\n💰 Testing budget reallocation with real volumes...")
        reallocation_result = manager.reallocate_budget("development", 0.02)  # Very low target to force reallocation
        
        if reallocation_result["reallocation_applied"]:
            print(f"✅ Budget reallocation working: ${reallocation_result['cost_reduction_needed']:.2f} reduction needed")
            print(f"  Original cost: ${reallocation_result['original_cost']:.2f}")
            print(f"  Target cost: ${reallocation_result['target_cost']:.2f}")
            print(f"  Total actions: {reallocation_result['total_actions']}")
            print(f"  Estimated savings: ${reallocation_result['estimated_savings']:.2f}")
            print(f"  Real volumes used: {sum(reallocation_result['real_volumes_used'].values()):.3f} GB total")
            for action in reallocation_result["actions"]:
                if action["action"] == "storage_tier_change":
                    print(f"    {action['rule']}: {action['from_tier']} → {action['to_tier']} (${action['estimated_savings']:.3f} savings, {action['real_volume_gb']:.3f} GB)")
                elif action["action"] == "retention_reduction":
                    print(f"    {action['rule']}: {action['from_period']} → {action['to_period']} (${action['estimated_savings']:.3f} savings, {action['real_volume_gb']:.3f} GB)")
        else:
            print(f"❌ Budget reallocation failed: {reallocation_result['reason']}")
        
        print("✅ Real-world volume integration test complete")
        sys.exit(0)
    
    # Check for test-reallocation flag
    if "--test-reallocation" in sys.argv:
        print("🔄 Testing budget reallocation mechanisms...")
        
        # Test budget reallocation
        print("\n💰 Testing budget reallocation...")
        reallocation_result = manager.reallocate_budget("development", 0.02)  # Very low target to force reallocation
        
        if reallocation_result["reallocation_applied"]:
            print(f"✅ Budget reallocation working: ${reallocation_result['cost_reduction_needed']:.2f} reduction needed")
            print(f"  Original cost: ${reallocation_result['original_cost']:.2f}")
            print(f"  Target cost: ${reallocation_result['target_cost']:.2f}")
            print(f"  Total actions: {reallocation_result['total_actions']}")
            print(f"  Estimated savings: ${reallocation_result['estimated_savings']:.2f}")
            for action in reallocation_result["actions"]:
                if action["action"] == "storage_tier_change":
                    print(f"    {action['rule']}: {action['from_tier']} → {action['to_tier']} (${action['estimated_savings']:.3f} savings)")
                elif action["action"] == "retention_reduction":
                    print(f"    {action['rule']}: {action['from_period']} → {action['to_period']} (${action['estimated_savings']:.3f} savings)")
        else:
            print(f"❌ Budget reallocation failed: {reallocation_result['reason']}")
        
        print("✅ Budget reallocation test complete")
        sys.exit(0)
    
    # Test cost estimation
    print("💰 Testing cost estimation...")
    # Use real volume data from Prometheus integration
    try:
        volume_data = manager.real_world_manager.get_real_data_volumes("production", hours=24)
        test_volumes = volume_data["volumes"]
        print(f"  Data source: {volume_data['data_source']}")
        print(f"  Confidence: {volume_data['confidence']:.1%}")
    except Exception as e:
        print(f"  Warning: Could not get real data ({e}), using fallback values")
        test_volumes = {
            "log": 1.5,      # Fallback: 1.5 GB/day
            "metric": 0.8,   # Fallback: 0.8 GB/day
            "trace": 0.3,    # Fallback: 0.3 GB/day
            "error": 0.1,    # Fallback: 0.1 GB/day
            "performance": 0.5,  # Fallback: 0.5 GB/day
            "security": 0.05,    # Fallback: 0.05 GB/day
            "audit": 0.02        # Fallback: 0.02 GB/day
        }
    
    for env in ["development", "staging", "production"]:
        policy = manager.get_policy(env)
        if policy:
            cost_estimate = manager.estimate_storage_cost(policy, test_volumes)
            target_budget = policy.budget_limit.total_cost_per_month if policy.budget_limit else "None"
            estimated_cost = cost_estimate["total_monthly_cost"]
            print(f"  {env}: {len(policy.rules)} rules, target: ${target_budget}/month, estimated: ${estimated_cost:.2f}/month")
            print(f"    Budget utilization: {cost_estimate['budget_utilization']:.1%}")
    
    # Test budget compliance
    print("\n🔍 Testing budget compliance...")
    # Use real cost data from API integration
    real_cost_data = manager.real_world_manager.get_real_cost_data("staging", days=7)
    test_costs = {
        "storage": real_cost_data.get("storage_cost", 45.0),
        "query": real_cost_data.get("query_cost", 12.0),
        "ingestion": real_cost_data.get("ingestion_cost", 8.0)
    }
    
    compliance = manager.check_budget_compliance("staging", test_costs)
    print(f"  Staging compliance: {'✅' if compliance['compliant'] else '❌'}")
    print(f"    Total cost: ${compliance['total_cost']:.2f}")
    print(f"    Budget utilization: {compliance['utilization']:.1%}")
    
    # Test optimization
    print("\n🎯 Testing retention optimization...")
    # Use real cost data multiplied by factor to simulate high costs
    high_cost_data = manager.real_world_manager.get_real_cost_data("staging", days=7)
    high_costs = {
        "storage": high_cost_data.get("storage_cost", 45.0) * 3.0,  # 3x higher than real
        "query": high_cost_data.get("query_cost", 12.0) * 2.5,     # 2.5x higher
        "ingestion": high_cost_data.get("ingestion_cost", 8.0) * 2.5  # 2.5x higher
    }
    
    optimization = manager.optimize_retention("staging", high_costs, 80.0)
    if optimization.get("optimized"):
        print(f"  Cost reduction needed: ${optimization['cost_reduction_needed']:.2f}")
        print(f"  Top suggestions:")
        for i, suggestion in enumerate(optimization["suggestions"][:3]):
            print(f"    {i+1}. {suggestion['type']}: {suggestion['rule']} - Save ${suggestion['estimated_savings']:.2f}")
    
    # Save policies
    print("\n💾 Saving retention policies...")
    for env, policy in manager.policies.items():
        manager.save_policy(policy)
    
    print("✅ Retention budget system test complete")