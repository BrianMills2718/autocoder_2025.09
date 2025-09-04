#!/usr/bin/env python3
"""
Unified Observability Economics Manager

Implements unified management of observability economics across sampling and retention
policies to provide coordinated cost optimization and budget enforcement.
"""

import logging
from typing import Dict, Any, Optional
from autocoder_cc.observability.sampling_policy import SamplingPolicyManager
from autocoder_cc.observability.retention_budget import RetentionBudgetManager, CostOptimizationEngine

class UnifiedEconomicsManager:
    """Unified management of observability economics across sampling and retention"""
    
    def __init__(self):
        self.sampling_manager = SamplingPolicyManager()
        self.retention_manager = RetentionBudgetManager()
        self.cost_optimizer = CostOptimizationEngine(self.retention_manager)
        self.logger = logging.getLogger(__name__)
        
        # Real-world data integration
        from autocoder_cc.observability.real_world_integrations import RealWorldDataManager
        self.real_world_manager = RealWorldDataManager()
    
    def optimize_total_cost(self, environment: str, target_cost: float) -> Dict[str, Any]:
        """Optimize both sampling and retention using real-world data"""
        # Get current policies
        sampling_policy = self.sampling_manager.get_policy(environment)
        retention_policy = self.retention_manager.get_policy(environment)
        
        if not sampling_policy or not retention_policy:
            return {"optimization_applied": False, "reason": "Policies not found"}
        
        # Calculate costs using real data
        sampling_cost_estimate = self.sampling_manager._estimate_cost(sampling_policy)
        current_sampling_cost = sampling_cost_estimate["total_per_month"]
        
        # Get real volumes for retention cost
        volume_data = self.real_world_manager.get_real_data_volumes(environment)
        real_volumes = volume_data["volumes"]
        retention_cost_estimate = self.retention_manager.estimate_storage_cost(retention_policy, real_volumes)
        current_retention_cost = retention_cost_estimate["total_monthly_cost"]
        
        total_current_cost = current_sampling_cost + current_retention_cost
        
        if total_current_cost <= target_cost:
            return {
                "optimization_applied": False,
                "reason": "Already within target cost",
                "current_sampling_cost": current_sampling_cost,
                "current_retention_cost": current_retention_cost,
                "total_current_cost": total_current_cost,
                "target_cost": target_cost,
                "data_source": sampling_cost_estimate.get("data_source", "real-world"),
                "real_volumes": real_volumes
            }
        
        # Perform unified optimization
        optimization_result = self.cost_optimizer.unified_optimization(
            environment, target_cost, current_sampling_cost, current_retention_cost
        )
        
        # If sampling reduction is needed, apply it using real cost data
        sampling_actions = []
        if optimization_result["sampling_reduction_needed"] > 0:
            # Get real cost data for budget enforcement
            real_costs = self.real_world_manager.get_real_costs(environment, days=7)
            
            # Use real cost data for enforcement
            current_costs = {
                "sampling": current_sampling_cost,
                "storage": real_costs.storage_cost,
                "query": real_costs.query_cost,
                "ingestion": real_costs.ingestion_cost
            }
            
            sampling_enforcement = self.sampling_manager.enforce_budget_limits(environment, current_costs)
            
            if sampling_enforcement["enforcement_applied"]:
                sampling_actions = sampling_enforcement["actions"]
        
        self.logger.info(f"Unified cost optimization applied to {environment}: ${optimization_result['total_cost_reduction_needed']:.2f} reduction needed")
        
        return {
            "optimization_applied": True,
            "environment": environment,
            "target_cost": target_cost,
            "original_sampling_cost": current_sampling_cost,
            "original_retention_cost": current_retention_cost,
            "total_original_cost": total_current_cost,
            "cost_reduction_needed": optimization_result["total_cost_reduction_needed"],
            "retention_savings": optimization_result["retention_savings"],
            "sampling_reduction_needed": optimization_result["sampling_reduction_needed"],
            "retention_actions": optimization_result["optimization_actions"]["retention_actions"],
            "sampling_actions": sampling_actions,
            "total_actions": len(optimization_result["optimization_actions"]["retention_actions"]) + len(sampling_actions),
            "data_source": sampling_cost_estimate.get("data_source", "real-world"),
            "real_volumes": real_volumes
        }
    
    def get_unified_budget_status(self, environment: str) -> Dict[str, Any]:
        """Get unified budget status using real-world data"""
        sampling_policy = self.sampling_manager.get_policy(environment)
        retention_policy = self.retention_manager.get_policy(environment)
        
        if not sampling_policy or not retention_policy:
            return {"status": "error", "reason": "Policies not found"}
        
        # Get budget limits
        sampling_budget = sampling_policy.budget_limit.total_cost_per_month if sampling_policy.budget_limit else 0
        retention_budget = retention_policy.budget_limit.total_cost_per_month if retention_policy.budget_limit else 0
        total_budget = sampling_budget + retention_budget
        
        # Estimate current costs using real data
        sampling_cost_estimate = self.sampling_manager._estimate_cost(sampling_policy)
        current_sampling_cost = sampling_cost_estimate["total_per_month"]
        
        # Get real volumes for retention cost
        volume_data = self.real_world_manager.get_real_data_volumes(environment)
        real_volumes = volume_data["volumes"]
        retention_cost_estimate = self.retention_manager.estimate_storage_cost(retention_policy, real_volumes)
        current_retention_cost = retention_cost_estimate["total_monthly_cost"]
        
        total_current_cost = current_sampling_cost + current_retention_cost
        
        # Calculate utilization
        budget_utilization = total_current_cost / total_budget if total_budget > 0 else 0
        
        return {
            "status": "success",
            "environment": environment,
            "sampling_budget": sampling_budget,
            "retention_budget": retention_budget,
            "total_budget": total_budget,
            "current_sampling_cost": current_sampling_cost,
            "current_retention_cost": current_retention_cost,
            "total_current_cost": total_current_cost,
            "budget_utilization": budget_utilization,
            "within_budget": total_current_cost <= total_budget,
            "sampling_rules": len(sampling_policy.rules),
            "retention_rules": len(retention_policy.rules),
            "data_source": sampling_cost_estimate.get("data_source", "real-world"),
            "real_volumes": real_volumes
        }
    
    def enforce_unified_compliance(self, environment: str) -> Dict[str, Any]:
        """Enforce compliance across both sampling and retention policies"""
        sampling_policy = self.sampling_manager.get_policy(environment)
        retention_policy = self.retention_manager.get_policy(environment)
        
        if not sampling_policy or not retention_policy:
            return {"enforcement_applied": False, "reason": "Policies not found"}
        
        compliance_actions = []
        
        # Check sampling compliance (critical data must be 100% sampled)
        for rule in sampling_policy.rules:
            if rule.type.value in ["error", "security", "audit"]:
                if rule.rate < 1.0:
                    original_rate = rule.rate
                    rule.rate = 1.0
                    compliance_actions.append({
                        "policy": "sampling",
                        "rule": rule.name,
                        "type": rule.type.value,
                        "action": "rate_correction",
                        "original_rate": original_rate,
                        "new_rate": 1.0
                    })
        
        # Check retention compliance (critical data must have long retention)
        for rule in retention_policy.rules:
            if rule.obs_type in ["error", "security", "audit"]:
                if rule.obs_type in ["security", "audit"] and rule.get_retention_days() < 365:
                    original_period = rule.retention_period.value
                    rule.retention_period = rule.retention_period.DAYS_365
                    compliance_actions.append({
                        "policy": "retention",
                        "rule": rule.name,
                        "type": rule.obs_type,
                        "action": "retention_correction",
                        "original_period": original_period,
                        "new_period": "365d"
                    })
        
        if compliance_actions:
            self.logger.warning(f"Compliance enforcement applied to {environment}: {len(compliance_actions)} violations corrected")
        
        return {
            "enforcement_applied": len(compliance_actions) > 0,
            "violations_corrected": len(compliance_actions),
            "actions": compliance_actions
        }

# Default unified economics manager instance
default_unified_manager = UnifiedEconomicsManager()

def get_unified_budget_status(environment: str) -> Dict[str, Any]:
    """Get unified budget status for environment"""
    return default_unified_manager.get_unified_budget_status(environment)

def optimize_total_cost(environment: str, target_cost: float) -> Dict[str, Any]:
    """Optimize total cost for environment"""
    return default_unified_manager.optimize_total_cost(environment, target_cost)

def enforce_unified_compliance(environment: str) -> Dict[str, Any]:
    """Enforce unified compliance for environment"""
    return default_unified_manager.enforce_unified_compliance(environment)

if __name__ == "__main__":
    import sys
    
    # Test the unified economics system
    manager = UnifiedEconomicsManager()
    
    # Check for test-real-integration flag
    if "--test-real-integration" in sys.argv:
        print("🌍 Testing real-world integration...")
        
        # Test unified budget status with real data
        print("\n📊 Testing unified budget status with real data...")
        for env in ["development", "staging", "production"]:
            status = manager.get_unified_budget_status(env)
            if status["status"] == "success":
                print(f"✅ {env}: total budget ${status['total_budget']:.0f}, current cost ${status['total_current_cost']:.2f}")
                print(f"  Data source: {status['data_source']}")
                print(f"  Real volumes: {sum(status['real_volumes'].values()):.3f} GB total")
                print(f"  Sampling: budget ${status['sampling_budget']:.0f}, cost ${status['current_sampling_cost']:.2f}")
                print(f"  Retention: budget ${status['retention_budget']:.0f}, cost ${status['current_retention_cost']:.2f}")
                print(f"  Utilization: {status['budget_utilization']:.1%}, within budget: {status['within_budget']}")
            else:
                print(f"❌ {env}: {status['reason']}")
        
        # Test unified cost optimization with real data
        print("\n🎯 Testing unified cost optimization with real data...")
        optimization_result = manager.optimize_total_cost("production", 2.0)  # Very low target
        
        if optimization_result["optimization_applied"]:
            print(f"✅ Unified optimization working: ${optimization_result['cost_reduction_needed']:.2f} reduction needed")
            print(f"  Data source: {optimization_result['data_source']}")
            print(f"  Real volumes: {sum(optimization_result['real_volumes'].values()):.3f} GB total")
            print(f"  Original total cost: ${optimization_result['total_original_cost']:.2f}")
            print(f"  Target cost: ${optimization_result['target_cost']:.2f}")
            print(f"  Retention savings: ${optimization_result['retention_savings']:.2f}")
            print(f"  Sampling reduction needed: ${optimization_result['sampling_reduction_needed']:.2f}")
            print(f"  Total actions: {optimization_result['total_actions']}")
        else:
            print(f"❌ Unified optimization failed: {optimization_result['reason']}")
            if "data_source" in optimization_result:
                print(f"  Data source: {optimization_result['data_source']}")
        
        print("✅ Real-world integration test complete")
        sys.exit(0)
    
    # Check for test-coordination flag
    if "--test-coordination" in sys.argv:
        print("🔗 Testing unified economics coordination...")
        
        # Test unified budget status
        print("\n📊 Testing unified budget status...")
        for env in ["development", "staging", "production"]:
            status = manager.get_unified_budget_status(env)
            if status["status"] == "success":
                print(f"✅ {env}: total budget ${status['total_budget']:.0f}, current cost ${status['total_current_cost']:.2f}")
                print(f"  Sampling: budget ${status['sampling_budget']:.0f}, cost ${status['current_sampling_cost']:.2f}")
                print(f"  Retention: budget ${status['retention_budget']:.0f}, cost ${status['current_retention_cost']:.2f}")
                print(f"  Utilization: {status['budget_utilization']:.1%}, within budget: {status['within_budget']}")
            else:
                print(f"❌ {env}: {status['reason']}")
        
        # Test unified cost optimization
        print("\n🎯 Testing unified cost optimization...")
        optimization_result = manager.optimize_total_cost("production", 2.0)  # Very low target
        
        if optimization_result["optimization_applied"]:
            print(f"✅ Unified optimization working: ${optimization_result['cost_reduction_needed']:.2f} reduction needed")
            print(f"  Original total cost: ${optimization_result['total_original_cost']:.2f}")
            print(f"  Target cost: ${optimization_result['target_cost']:.2f}")
            print(f"  Retention savings: ${optimization_result['retention_savings']:.2f}")
            print(f"  Sampling reduction needed: ${optimization_result['sampling_reduction_needed']:.2f}")
            print(f"  Total actions: {optimization_result['total_actions']}")
        else:
            print(f"❌ Unified optimization failed: {optimization_result['reason']}")
        
        # Test unified compliance enforcement
        print("\n🛡️ Testing unified compliance enforcement...")
        compliance_result = manager.enforce_unified_compliance("production")
        
        if compliance_result["enforcement_applied"]:
            print(f"✅ Compliance enforcement working: {compliance_result['violations_corrected']} violations corrected")
            for action in compliance_result["actions"]:
                print(f"  {action['policy']} - {action['rule']}: {action['action']}")
        else:
            print("✅ No compliance violations found")
        
        print("✅ Unified economics coordination test complete")
        sys.exit(0)
    
    # Test unified budget status
    print("🔗 Testing unified economics system...")
    for env in ["development", "staging", "production"]:
        status = manager.get_unified_budget_status(env)
        if status["status"] == "success":
            print(f"  {env}: total budget ${status['total_budget']:.0f}, current cost ${status['total_current_cost']:.2f} ({status['budget_utilization']:.1%})")
    
    print("✅ Unified economics system test complete")