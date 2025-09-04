# Migration Strategy: RPC to Port-Based Architecture

## Overview
This document provides a comprehensive strategy for migrating 52 existing RPC-based systems to the new port-based architecture while maintaining system availability and enabling rollback if needed.

## 1. Current State Assessment

### 1.1 Existing Systems Inventory
```bash
# Current systems in generated_systems/
Total Systems: 52
Date Range: 2025-07-22 to 2025-08-06
Validation Success Rate: 27.8%
Common Failures: Import errors, component communication issues
```

### 1.2 System Categories
```python
SYSTEM_CATEGORIES = {
    "todo_systems": 15,      # Todo management variations
    "api_systems": 12,       # REST API systems  
    "data_processing": 8,    # ETL and processing pipelines
    "monitoring": 5,         # Monitoring and alerting
    "experimental": 12       # Test and experimental systems
}
```

### 1.3 Migration Priority
```python
MIGRATION_PRIORITY = {
    "P0": ["todo_api_system"],           # Most used, simplest
    "P1": ["simple_rest_api", "hello_world_api"],  # Well understood
    "P2": ["data_processing_*"],         # Medium complexity
    "P3": ["monitoring_*"],              # Complex dependencies
    "P4": ["experimental_*"]             # Can afford failures
}
```

## 2. Migration Strategy

### 2.1 Phased Approach
```yaml
migration_phases:
  phase_1_pilot:
    duration: 3 days
    systems: 1-3 (P0 systems)
    goal: Validate new architecture works
    rollback: Easy, minimal impact
    
  phase_2_expansion:
    duration: 1 week
    systems: 4-15 (P1 systems)
    goal: Prove at scale
    rollback: Still feasible
    
  phase_3_majority:
    duration: 1 week
    systems: 16-40 (P2-P3 systems)
    goal: Migrate majority
    rollback: Difficult but possible
    
  phase_4_completion:
    duration: 3 days
    systems: 41-52 (P4 systems)
    goal: Complete migration
    rollback: Forward only
```

### 2.2 Parallel Run Strategy
```python
class ParallelRunManager:
    """Manage parallel execution of old and new systems"""
    
    def __init__(self):
        self.old_systems = {}
        self.new_systems = {}
        self.comparison_results = {}
        
    async def run_parallel(
        self,
        system_name: str,
        duration_hours: int = 24
    ) -> Dict[str, Any]:
        """Run old and new systems in parallel"""
        
        # Start old system (RPC-based)
        old_system = await self.start_old_system(system_name)
        
        # Start new system (Port-based)
        new_system = await self.start_new_system(system_name)
        
        # Route traffic to both
        await self.setup_traffic_mirroring(system_name)
        
        # Collect metrics
        start_time = time.monotonic()
        metrics = {"old": [], "new": []}
        
        while time.monotonic() - start_time < duration_hours * 3600:
            metrics["old"].append(await old_system.get_metrics())
            metrics["new"].append(await new_system.get_metrics())
            await anyio.sleep(60)  # Check every minute
            
        # Compare results
        comparison = self.compare_systems(metrics)
        
        # Decision point
        if comparison["new_better"]:
            await self.promote_new_system(system_name)
        else:
            await self.rollback_to_old(system_name)
            
        return comparison
    
    def compare_systems(self, metrics: Dict) -> Dict[str, Any]:
        """Compare old vs new system performance"""
        old_metrics = metrics["old"]
        new_metrics = metrics["new"]
        
        comparison = {
            "throughput_improvement": self.calculate_improvement(
                old_metrics, new_metrics, "throughput"
            ),
            "latency_improvement": self.calculate_improvement(
                old_metrics, new_metrics, "latency"
            ),
            "error_rate_change": self.calculate_improvement(
                old_metrics, new_metrics, "error_rate"
            ),
            "validation_success": self.check_validation_success(new_metrics),
            "new_better": False
        }
        
        # New is better if validation > 80% and no performance regression
        comparison["new_better"] = (
            comparison["validation_success"] >= 0.8 and
            comparison["throughput_improvement"] >= -0.05 and  # Allow 5% regression
            comparison["latency_improvement"] <= 0.10  # Allow 10% increase
        )
        
        return comparison
```

## 3. Migration Process

### 3.1 Pre-Migration Checklist
```python
class PreMigrationChecklist:
    """Validate system ready for migration"""
    
    def check_system(self, system_name: str) -> Dict[str, bool]:
        """Run pre-migration checks"""
        checks = {
            "backup_exists": self.check_backup(system_name),
            "tests_passing": self.check_tests(system_name),
            "dependencies_mapped": self.check_dependencies(system_name),
            "rollback_plan": self.check_rollback_plan(system_name),
            "monitoring_setup": self.check_monitoring(system_name),
            "team_notified": self.check_team_notification(system_name)
        }
        
        checks["ready_to_migrate"] = all(checks.values())
        return checks
    
    def check_backup(self, system_name: str) -> bool:
        """Ensure backup exists"""
        backup_path = Path(f"backups/{system_name}_{datetime.now().strftime('%Y%m%d')}")
        if not backup_path.exists():
            # Create backup
            shutil.copytree(
                f"generated_systems/{system_name}",
                backup_path
            )
        return backup_path.exists()
    
    def check_rollback_plan(self, system_name: str) -> bool:
        """Ensure rollback plan documented"""
        rollback_file = Path(f"migration/rollback/{system_name}.md")
        return rollback_file.exists()
```

### 3.2 Migration Execution
```python
class SystemMigrator:
    """Execute system migration"""
    
    def __init__(self):
        self.blueprint_processor = BlueprintProcessor()
        self.validator = PortBasedValidationGate()
        self.deployer = SystemDeployer()
        
    async def migrate_system(
        self,
        system_name: str,
        strategy: str = "blue_green"
    ) -> MigrationResult:
        """Migrate a single system"""
        
        print(f"🔄 Starting migration for {system_name}")
        
        # Step 1: Load existing blueprint
        old_blueprint = self.load_blueprint(f"generated_systems/{system_name}")
        
        # Step 2: Convert to port-based blueprint
        new_blueprint = self.convert_blueprint(old_blueprint)
        
        # Step 3: Generate new system
        new_system_path = await self.generate_new_system(
            new_blueprint,
            f"generated_systems_v2/{system_name}"
        )
        
        # Step 4: Validate new system
        validation_result = await self.validator.validate_system(
            new_system_path / "components",
            new_blueprint,
            system_name
        )
        
        if validation_result.validation_success_rate < 0.8:
            print(f"❌ Validation failed: {validation_result.validation_success_rate:.1%}")
            return MigrationResult(
                success=False,
                reason="Validation failed",
                rollback_needed=False
            )
        
        # Step 5: Deploy with strategy
        if strategy == "blue_green":
            result = await self.blue_green_deploy(system_name, new_system_path)
        elif strategy == "canary":
            result = await self.canary_deploy(system_name, new_system_path)
        else:
            result = await self.direct_deploy(system_name, new_system_path)
        
        return result
    
    def convert_blueprint(self, old_blueprint: Dict) -> Dict:
        """Convert RPC blueprint to port-based"""
        new_blueprint = {
            "schema_version": "2.0.0",  # New version
            "system": {
                "name": old_blueprint["system"]["name"],
                "description": old_blueprint["system"]["description"],
                "version": old_blueprint["system"]["version"]
            },
            "components": [],
            "bindings": []
        }
        
        # Convert components
        for component in old_blueprint["system"]["components"]:
            new_component = self.convert_component(component)
            new_blueprint["components"].append(new_component)
        
        # Generate bindings from old connections
        new_blueprint["bindings"] = self.generate_bindings(
            old_blueprint["system"]["components"]
        )
        
        return new_blueprint
    
    def convert_component(self, old_component: Dict) -> Dict:
        """Convert single component to recipe-based"""
        # Map old type to recipe
        type_to_recipe = {
            "DataStore": "Store",
            "APIGateway": "APIEndpoint",
            "Controller": "Controller",
            "Router": "Router",
            "Aggregator": "Aggregator",
            "Filter": "Filter",
            "Processor": "Transformer"
        }
        
        recipe = type_to_recipe.get(
            old_component["type"],
            "Transformer"  # Default
        )
        
        return {
            "name": old_component["name"],
            "recipe": recipe,
            "config": old_component.get("configuration", {})
        }
    
    async def blue_green_deploy(
        self,
        system_name: str,
        new_system_path: Path
    ) -> MigrationResult:
        """Blue-green deployment strategy"""
        
        # Deploy new (green) alongside old (blue)
        green_url = await self.deployer.deploy(
            new_system_path,
            f"{system_name}-green"
        )
        
        # Test green deployment
        test_result = await self.test_deployment(green_url)
        
        if test_result["success"]:
            # Switch traffic
            await self.switch_traffic(system_name, green_url)
            
            # Monitor for issues
            await anyio.sleep(300)  # 5 minutes
            
            if await self.check_health(green_url):
                # Decommission blue
                await self.decommission_old(f"{system_name}-blue")
                return MigrationResult(success=True)
            else:
                # Rollback
                await self.switch_traffic(system_name, f"{system_name}-blue")
                return MigrationResult(
                    success=False,
                    reason="Health check failed",
                    rollback_needed=True
                )
        
        return MigrationResult(
            success=False,
            reason="Test failed",
            rollback_needed=False
        )
```

## 4. Rollback Plan

### 4.1 Rollback Triggers
```yaml
rollback_triggers:
  automatic:
    - validation_success_rate < 0.7
    - error_rate > 0.05
    - latency_p95 > 2x_baseline
    - throughput < 0.5x_baseline
    - health_check_failures > 3
    
  manual:
    - team_decision
    - customer_impact
    - data_corruption_risk
```

### 4.2 Rollback Procedure
```python
class RollbackManager:
    """Manage system rollbacks"""
    
    async def rollback_system(
        self,
        system_name: str,
        reason: str
    ) -> bool:
        """Execute rollback for a system"""
        
        print(f"⚠️ Initiating rollback for {system_name}: {reason}")
        
        # Step 1: Stop new system
        await self.stop_new_system(system_name)
        
        # Step 2: Restore old system
        backup_path = self.get_latest_backup(system_name)
        await self.restore_system(backup_path, system_name)
        
        # Step 3: Restart old system
        await self.start_old_system(system_name)
        
        # Step 4: Verify old system working
        if await self.verify_system(system_name):
            print(f"✅ Rollback successful for {system_name}")
            
            # Step 5: Document failure
            self.document_failure(system_name, reason)
            
            return True
        else:
            print(f"❌ Rollback failed for {system_name}")
            # Emergency procedure
            await self.emergency_recovery(system_name)
            return False
    
    def document_failure(self, system_name: str, reason: str):
        """Document migration failure for analysis"""
        failure_doc = {
            "system": system_name,
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "logs": self.collect_logs(system_name),
            "metrics": self.collect_metrics(system_name)
        }
        
        with open(f"migration/failures/{system_name}_{datetime.now():%Y%m%d_%H%M%S}.json", 'w') as f:
            json.dump(failure_doc, f, indent=2)
```

## 5. Migration Timeline

### 5.1 Detailed Schedule
```yaml
week_1:
  monday:
    - Fix import bugs in ast_self_healing.py
    - Implement port base classes
    - Create first recipe expander
    
  tuesday:
    - Complete 5 mathematical primitives
    - Implement recipe expansion for all 13 types
    - Create migration tooling
    
  wednesday:
    - Migrate first P0 system (todo_api_system)
    - Run parallel validation for 24 hours
    - Document results
    
  thursday:
    - Fix issues found in P0 migration
    - Migrate 2 more P0 systems
    - Update migration playbook
    
  friday:
    - Migrate all P1 systems (5-8 systems)
    - Run weekend validation

week_2:
  monday:
    - Review weekend results
    - Fix any issues found
    - Start P2 migration (10 systems)
    
  tuesday-thursday:
    - Continue P2/P3 migration
    - Target: 5-8 systems per day
    - Continuous validation
    
  friday:
    - Complete P3 systems
    - Prepare for final push

week_3:
  monday-tuesday:
    - Migrate remaining P4 systems
    - Full system validation
    
  wednesday:
    - Decommission old systems
    - Update documentation
    - Clean up code
    
  thursday-friday:
    - Performance testing
    - Final validation
    - Release preparation
```

## 6. Success Metrics

### 6.1 Migration KPIs
```python
@dataclass
class MigrationMetrics:
    """Track migration success"""
    
    # Progress metrics
    systems_migrated: int = 0
    systems_total: int = 52
    migration_rate: float = 0.0  # systems/day
    
    # Quality metrics
    validation_success_rate: float = 0.0  # Target: 80%
    rollback_count: int = 0  # Target: <5
    failed_migrations: int = 0  # Target: 0
    
    # Performance metrics
    avg_throughput_improvement: float = 0.0  # Target: +20%
    avg_latency_change: float = 0.0  # Target: <+10%
    
    # Time metrics
    avg_migration_time_hours: float = 0.0  # Target: <2
    total_downtime_minutes: float = 0.0  # Target: 0
    
    def calculate_success_score(self) -> float:
        """Calculate overall migration success score"""
        scores = [
            self.systems_migrated / self.systems_total,
            self.validation_success_rate,
            1.0 - (self.rollback_count / max(self.systems_migrated, 1)),
            1.0 if self.failed_migrations == 0 else 0.5,
            min(1.0, max(0.0, self.avg_throughput_improvement + 1.0)),
            1.0 if self.total_downtime_minutes == 0 else 0.8
        ]
        return sum(scores) / len(scores)
```

## 7. Risk Mitigation

### 7.1 Risk Matrix
```yaml
risks:
  high:
    - description: "Data loss during migration"
      mitigation: "Complete backups, parallel run, validation"
      owner: "DevOps"
      
    - description: "Performance regression"
      mitigation: "Extensive benchmarking, gradual rollout"
      owner: "Performance Team"
      
  medium:
    - description: "Import errors in new code"
      mitigation: "Fix known bugs first, extensive testing"
      owner: "Dev Team"
      
    - description: "Team knowledge gap"
      mitigation: "Documentation, training, pair programming"
      owner: "Tech Lead"
      
  low:
    - description: "Rollback complexity"
      mitigation: "Automated rollback, clear procedures"
      owner: "DevOps"
```

### 7.2 Contingency Plans
```python
class ContingencyPlans:
    """Contingency plans for migration issues"""
    
    def data_corruption_detected(self):
        """Response to data corruption"""
        return [
            "1. Immediately stop migration",
            "2. Isolate affected systems",
            "3. Restore from backup",
            "4. Run data integrity checks",
            "5. Root cause analysis",
            "6. Fix and re-test before continuing"
        ]
    
    def performance_degradation(self):
        """Response to performance issues"""
        return [
            "1. Enable detailed profiling",
            "2. Identify bottleneck component",
            "3. Scale affected components",
            "4. Optimize hot paths",
            "5. Consider partial rollback",
            "6. Re-benchmark before continuing"
        ]
    
    def mass_failure(self):
        """Response to multiple system failures"""
        return [
            "1. Initiate emergency rollback",
            "2. Restore all systems to previous state",
            "3. All-hands debugging session",
            "4. Identify common failure pattern",
            "5. Fix root cause",
            "6. Restart migration with smaller batch"
        ]
```

## 8. Post-Migration Tasks

### 8.1 Cleanup Checklist
```yaml
post_migration_cleanup:
  code:
    - Remove old RPC implementation
    - Delete deprecated component types
    - Clean up unused dependencies
    - Archive old test files
    
  infrastructure:
    - Decommission old deployments
    - Clean up unused resources
    - Update monitoring dashboards
    - Archive old logs
    
  documentation:
    - Update all docs to port-based
    - Archive migration docs
    - Update onboarding materials
    - Create post-mortem report
```

### 8.2 Optimization Opportunities
```python
class PostMigrationOptimizer:
    """Optimize systems after migration"""
    
    def identify_optimizations(self) -> List[Dict]:
        """Find optimization opportunities"""
        return [
            {
                "area": "Buffer Sizes",
                "action": "Tune based on actual usage patterns",
                "impact": "Memory efficiency"
            },
            {
                "area": "Concurrency",
                "action": "Adjust worker counts per component",
                "impact": "CPU utilization"
            },
            {
                "area": "Batch Sizes",
                "action": "Optimize for throughput vs latency",
                "impact": "Performance"
            },
            {
                "area": "Checkpoint Frequency",
                "action": "Balance durability vs performance",
                "impact": "Recovery time"
            }
        ]
```

## Summary

This migration strategy provides:

1. **Phased approach** minimizing risk
2. **Parallel run capability** for validation
3. **Automated rollback** for safety
4. **Clear success metrics** for decision making
5. **Comprehensive testing** at each phase
6. **Risk mitigation** strategies
7. **Post-migration optimization** plan

Total migration time: ~3 weeks
Target success rate: >95% of systems
Expected validation improvement: 27.8% → 80%+

---
> **📊 Status Note**: Status facts in this document are **non-authoritative**. See [06_DECISIONS/STATUS_SOT.md](06_DECISIONS/STATUS_SOT.md) for the single source of truth.
