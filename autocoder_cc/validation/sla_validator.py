"""
SLA Validator
Service Level Agreement validation framework based on measured performance data
"""

import time
import statistics
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from ..observability.structured_logging import get_logger
from ..observability.metrics import MetricsCollector
from ..core.exceptions import ValidationError


class SLAViolationType(Enum):
    LATENCY = "latency"
    AVAILABILITY = "availability"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"


@dataclass
class SLARequirement:
    """Single SLA requirement definition"""
    name: str
    metric_type: str
    threshold_value: float
    comparison_operator: str  # "lt", "le", "gt", "ge", "eq"
    measurement_window_seconds: int = 300  # 5 minutes
    violation_threshold_percent: float = 5.0  # 5% violations allowed
    description: str = ""


@dataclass
class SLAViolation:
    """SLA violation record"""
    requirement_name: str
    violation_type: SLAViolationType
    actual_value: float
    expected_value: float
    timestamp: datetime = field(default_factory=datetime.now)
    component: str = ""
    severity: str = "warning"
    description: str = ""


@dataclass
class SLAMetrics:
    """SLA metrics for a capability"""
    capability_name: str
    p99_latency_ms: float
    p95_latency_ms: float
    mean_latency_ms: float
    availability_percent: float
    error_rate_percent: float
    throughput_ops_per_sec: float
    measurement_window_start: datetime
    measurement_window_end: datetime
    sample_count: int


class SLAValidator:
    """SLA-based validation framework"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.metrics_collector = MetricsCollector()
        self.sla_requirements: Dict[str, List[SLARequirement]] = {}
        self.violations: List[SLAViolation] = []
        self.measurement_history: Dict[str, List[SLAMetrics]] = {}
        
        # Load default SLA requirements
        self._load_default_sla_requirements()
    
    def _load_default_sla_requirements(self):
        """Load default SLA requirements based on capability tiers"""
        
        # Ultra Fast tier (< 1ms)
        ultra_fast_capabilities = [
            "component_loading", "port_validation", "configuration_loading",
            "caching", "rate_limiting"
        ]
        
        for capability in ultra_fast_capabilities:
            self.sla_requirements[capability] = [
                SLARequirement(
                    name=f"{capability}_p99_latency",
                    metric_type="p99_latency_ms",
                    threshold_value=1.0,
                    comparison_operator="lt",
                    description=f"P99 latency must be less than 1ms for {capability}"
                ),
                SLARequirement(
                    name=f"{capability}_availability",
                    metric_type="availability_percent",
                    threshold_value=99.9,
                    comparison_operator="ge",
                    description=f"Availability must be >= 99.9% for {capability}"
                ),
                SLARequirement(
                    name=f"{capability}_error_rate",
                    metric_type="error_rate_percent",
                    threshold_value=0.1,
                    comparison_operator="lt",
                    description=f"Error rate must be < 0.1% for {capability}"
                )
            ]
        
        # Fast tier (1-10ms)
        fast_capabilities = [
            "component_initialization", "schema_validation", "data_transformation",
            "logging", "metrics_collection", "health_checks"
        ]
        
        for capability in fast_capabilities:
            self.sla_requirements[capability] = [
                SLARequirement(
                    name=f"{capability}_p99_latency",
                    metric_type="p99_latency_ms",
                    threshold_value=10.0,
                    comparison_operator="lt",
                    description=f"P99 latency must be less than 10ms for {capability}"
                ),
                SLARequirement(
                    name=f"{capability}_availability",
                    metric_type="availability_percent",
                    threshold_value=99.5,
                    comparison_operator="ge",
                    description=f"Availability must be >= 99.5% for {capability}"
                ),
                SLARequirement(
                    name=f"{capability}_error_rate",
                    metric_type="error_rate_percent",
                    threshold_value=0.5,
                    comparison_operator="lt",
                    description=f"Error rate must be < 0.5% for {capability}"
                )
            ]
        
        # Standard tier (10-100ms)
        standard_capabilities = [
            "error_handling", "security_validation", "resource_allocation",
            "circuit_breaker", "retry_mechanism", "event_processing"
        ]
        
        for capability in standard_capabilities:
            self.sla_requirements[capability] = [
                SLARequirement(
                    name=f"{capability}_p99_latency",
                    metric_type="p99_latency_ms",
                    threshold_value=100.0,
                    comparison_operator="lt",
                    description=f"P99 latency must be less than 100ms for {capability}"
                ),
                SLARequirement(
                    name=f"{capability}_availability",
                    metric_type="availability_percent",
                    threshold_value=99.0,
                    comparison_operator="ge",
                    description=f"Availability must be >= 99.0% for {capability}"
                ),
                SLARequirement(
                    name=f"{capability}_error_rate",
                    metric_type="error_rate_percent",
                    threshold_value=1.0,
                    comparison_operator="lt",
                    description=f"Error rate must be < 1.0% for {capability}"
                )
            ]
        
        # Slow tier (100-1000ms)
        slow_capabilities = [
            "async_processing", "api_endpoint", "database_operation", "file_system"
        ]
        
        for capability in slow_capabilities:
            self.sla_requirements[capability] = [
                SLARequirement(
                    name=f"{capability}_p99_latency",
                    metric_type="p99_latency_ms",
                    threshold_value=1000.0,
                    comparison_operator="lt",
                    description=f"P99 latency must be less than 1000ms for {capability}"
                ),
                SLARequirement(
                    name=f"{capability}_availability",
                    metric_type="availability_percent",
                    threshold_value=98.0,
                    comparison_operator="ge",
                    description=f"Availability must be >= 98.0% for {capability}"
                ),
                SLARequirement(
                    name=f"{capability}_error_rate",
                    metric_type="error_rate_percent",
                    threshold_value=2.0,
                    comparison_operator="lt",
                    description=f"Error rate must be < 2.0% for {capability}"
                )
            ]
    
    def add_sla_requirement(self, capability: str, requirement: SLARequirement):
        """Add SLA requirement for a capability"""
        if capability not in self.sla_requirements:
            self.sla_requirements[capability] = []
        
        self.sla_requirements[capability].append(requirement)
        self.logger.info(f"Added SLA requirement for {capability}: {requirement.name}")
    
    def validate_sla_metrics(self, capability: str, metrics: SLAMetrics) -> List[SLAViolation]:
        """Validate SLA metrics against requirements"""
        violations = []
        
        if capability not in self.sla_requirements:
            self.logger.warning(f"No SLA requirements defined for capability: {capability}")
            return violations
        
        for requirement in self.sla_requirements[capability]:
            violation = self._check_sla_requirement(capability, requirement, metrics)
            if violation:
                violations.append(violation)
        
        # Store violations
        self.violations.extend(violations)
        
        # Log violations
        for violation in violations:
            self.logger.warning(f"SLA violation: {violation.requirement_name} - "
                              f"actual: {violation.actual_value}, expected: {violation.expected_value}")
        
        return violations
    
    def _check_sla_requirement(self, capability: str, requirement: SLARequirement, 
                             metrics: SLAMetrics) -> Optional[SLAViolation]:
        """Check single SLA requirement"""
        
        # Get actual value for the metric
        actual_value = self._get_metric_value(metrics, requirement.metric_type)
        if actual_value is None:
            return None
        
        # Check requirement
        violation_detected = False
        
        if requirement.comparison_operator == "lt":
            violation_detected = actual_value >= requirement.threshold_value
        elif requirement.comparison_operator == "le":
            violation_detected = actual_value > requirement.threshold_value
        elif requirement.comparison_operator == "gt":
            violation_detected = actual_value <= requirement.threshold_value
        elif requirement.comparison_operator == "ge":
            violation_detected = actual_value < requirement.threshold_value
        elif requirement.comparison_operator == "eq":
            violation_detected = actual_value != requirement.threshold_value
        
        if violation_detected:
            # Determine violation type
            violation_type = SLAViolationType.LATENCY
            if "availability" in requirement.metric_type:
                violation_type = SLAViolationType.AVAILABILITY
            elif "error_rate" in requirement.metric_type:
                violation_type = SLAViolationType.ERROR_RATE
            elif "throughput" in requirement.metric_type:
                violation_type = SLAViolationType.THROUGHPUT
            
            # Determine severity
            severity = "warning"
            if actual_value > requirement.threshold_value * 2:
                severity = "error"
            elif actual_value > requirement.threshold_value * 5:
                severity = "critical"
            
            return SLAViolation(
                requirement_name=requirement.name,
                violation_type=violation_type,
                actual_value=actual_value,
                expected_value=requirement.threshold_value,
                component=capability,
                severity=severity,
                description=requirement.description
            )
        
        return None
    
    def _get_metric_value(self, metrics: SLAMetrics, metric_type: str) -> Optional[float]:
        """Get metric value from SLA metrics"""
        metric_map = {
            "p99_latency_ms": metrics.p99_latency_ms,
            "p95_latency_ms": metrics.p95_latency_ms,
            "mean_latency_ms": metrics.mean_latency_ms,
            "availability_percent": metrics.availability_percent,
            "error_rate_percent": metrics.error_rate_percent,
            "throughput_ops_per_sec": metrics.throughput_ops_per_sec
        }
        
        return metric_map.get(metric_type)
    
    def validate_capability_performance(self, capability: str, measurements: List[float]) -> List[SLAViolation]:
        """Validate capability performance measurements"""
        if not measurements:
            # FAIL FAST - No graceful degradation
            raise ValueError(
                f"CRITICAL: No measurements provided for capability '{capability}'. "
                "Cannot validate SLA without performance data."
            )
        
        # Calculate metrics
        metrics = SLAMetrics(
            capability_name=capability,
            p99_latency_ms=statistics.quantiles(measurements, n=100)[98] if len(measurements) > 1 else measurements[0],
            p95_latency_ms=statistics.quantiles(measurements, n=100)[94] if len(measurements) > 1 else measurements[0],
            mean_latency_ms=statistics.mean(measurements),
            availability_percent=100.0,  # Assume 100% if no failures
            error_rate_percent=0.0,      # Assume 0% if no errors
            throughput_ops_per_sec=len(measurements) / (len(measurements) * statistics.mean(measurements) / 1000),
            measurement_window_start=datetime.now() - timedelta(minutes=5),
            measurement_window_end=datetime.now(),
            sample_count=len(measurements)
        )
        
        # Store metrics
        if capability not in self.measurement_history:
            self.measurement_history[capability] = []
        self.measurement_history[capability].append(metrics)
        
        # Validate against SLA
        return self.validate_sla_metrics(capability, metrics)
    
    def get_sla_compliance_report(self, capability: Optional[str] = None) -> Dict[str, Any]:
        """Generate SLA compliance report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "compliance_summary": {},
            "violations": [],
            "capability_metrics": {}
        }
        
        # Filter violations by capability if specified
        relevant_violations = self.violations
        if capability:
            relevant_violations = [v for v in self.violations if v.component == capability]
        
        # Group violations by capability
        violations_by_capability = {}
        for violation in relevant_violations:
            cap = violation.component
            if cap not in violations_by_capability:
                violations_by_capability[cap] = []
            violations_by_capability[cap].append(violation)
        
        # Calculate compliance summary
        all_capabilities = set()
        if capability:
            all_capabilities.add(capability)
        else:
            all_capabilities.update(self.sla_requirements.keys())
            all_capabilities.update(violations_by_capability.keys())
        
        for cap in all_capabilities:
            cap_violations = violations_by_capability.get(cap, [])
            total_requirements = len(self.sla_requirements.get(cap, []))
            
            report["compliance_summary"][cap] = {
                "total_requirements": total_requirements,
                "violations_count": len(cap_violations),
                "compliance_percent": ((total_requirements - len(cap_violations)) / total_requirements * 100) if total_requirements > 0 else 100,
                "critical_violations": len([v for v in cap_violations if v.severity == "critical"]),
                "error_violations": len([v for v in cap_violations if v.severity == "error"]),
                "warning_violations": len([v for v in cap_violations if v.severity == "warning"])
            }
        
        # Add violation details
        for violation in relevant_violations:
            report["violations"].append({
                "requirement_name": violation.requirement_name,
                "violation_type": violation.violation_type.value,
                "component": violation.component,
                "actual_value": violation.actual_value,
                "expected_value": violation.expected_value,
                "severity": violation.severity,
                "timestamp": violation.timestamp.isoformat(),
                "description": violation.description
            })
        
        # Add capability metrics
        for cap, metrics_list in self.measurement_history.items():
            if capability and cap != capability:
                continue
            
            if metrics_list:
                latest_metrics = metrics_list[-1]
                report["capability_metrics"][cap] = {
                    "p99_latency_ms": latest_metrics.p99_latency_ms,
                    "p95_latency_ms": latest_metrics.p95_latency_ms,
                    "mean_latency_ms": latest_metrics.mean_latency_ms,
                    "availability_percent": latest_metrics.availability_percent,
                    "error_rate_percent": latest_metrics.error_rate_percent,
                    "throughput_ops_per_sec": latest_metrics.throughput_ops_per_sec,
                    "sample_count": latest_metrics.sample_count,
                    "measurement_window": {
                        "start": latest_metrics.measurement_window_start.isoformat(),
                        "end": latest_metrics.measurement_window_end.isoformat()
                    }
                }
        
        return report
    
    def enforce_sla_policies(self, capability: str, operation: Callable, *args, **kwargs):
        """Enforce SLA policies for a capability operation"""
        start_time = time.perf_counter()
        
        try:
            # Execute operation
            result = operation(*args, **kwargs)
            
            # Measure execution time
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            # Validate against SLA
            violations = self.validate_capability_performance(capability, [duration_ms])
            
            # Record metrics
            self.metrics_collector.record_histogram(
                f"sla_{capability}_duration_ms", 
                duration_ms, 
                {"capability": capability}
            )
            
            # Handle violations
            if violations:
                for violation in violations:
                    self.metrics_collector.increment_counter(
                        f"sla_violation_{violation.violation_type.value}",
                        1,
                        {"capability": capability, "severity": violation.severity}
                    )
                    
                    if violation.severity == "critical":
                        self.logger.error(f"Critical SLA violation: {violation.description}")
                    elif violation.severity == "error":
                        self.logger.error(f"SLA violation: {violation.description}")
                    else:
                        self.logger.warning(f"SLA violation: {violation.description}")
            
            return result
            
        except Exception as e:
            # Record error
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            self.metrics_collector.increment_counter(
                f"sla_{capability}_error",
                1,
                {"capability": capability, "error_type": type(e).__name__}
            )
            
            self.logger.error(f"SLA-enforced operation failed for {capability}: {str(e)}")
            raise
    
    def get_sla_requirements(self, capability: str) -> List[SLARequirement]:
        """Get SLA requirements for a capability"""
        return self.sla_requirements.get(capability, [])
    
    def clear_violations(self, capability: Optional[str] = None):
        """Clear violations for a capability or all capabilities"""
        if capability:
            self.violations = [v for v in self.violations if v.component != capability]
        else:
            self.violations = []
        
        self.logger.info(f"Cleared SLA violations for {capability or 'all capabilities'}")


def main():
    """Main CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SLA Validator")
    parser.add_argument("--capability", type=str, help="Capability to validate")
    parser.add_argument("--generate-report", action="store_true", help="Generate SLA compliance report")
    parser.add_argument("--output", type=str, help="Output file for report")
    
    args = parser.parse_args()
    
    validator = SLAValidator()
    
    if args.generate_report:
        report = validator.get_sla_compliance_report(args.capability)
        
        if args.output:
            import json
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"SLA compliance report saved to: {args.output}")
        else:
            import json
            print(json.dumps(report, indent=2))
    
    else:
        print("Use --generate-report to generate SLA compliance report")


if __name__ == "__main__":
    main()