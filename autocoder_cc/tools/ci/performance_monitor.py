#!/usr/bin/env python3
"""
Comprehensive Performance Monitoring and Benchmarking System
Measures execution times, resource usage, and provides statistical analysis
"""

import os
import sys
import time
import json
import psutil
import statistics
import subprocess
import threading
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, asdict
from contextlib import contextmanager


@dataclass
class PerformanceMetric:
    """Single performance measurement"""
    name: str
    value: float
    unit: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ResourceMetrics:
    """System resource usage metrics"""
    cpu_percent: float
    memory_usage_mb: float
    memory_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    timestamp: str


@dataclass
class PerformanceReport:
    """Comprehensive performance analysis report"""
    component_name: str
    test_scenario: str
    execution_time: float
    resource_metrics: ResourceMetrics
    performance_metrics: List[PerformanceMetric]
    statistical_analysis: Dict[str, Any]
    benchmark_comparison: Optional[Dict[str, Any]] = None
    timestamp: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class SystemMonitor:
    """Real-time system monitoring during test execution"""
    
    def __init__(self, sampling_interval: float = 0.1):
        self.sampling_interval = sampling_interval
        self.monitoring = False
        self.samples: List[ResourceMetrics] = []
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Get initial network and disk stats for delta calculation
        self._initial_net_io = psutil.net_io_counters()
        self._initial_disk_io = psutil.disk_io_counters()
    
    def start_monitoring(self):
        """Start resource monitoring in background thread"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.samples = []
        self._initial_net_io = psutil.net_io_counters()
        self._initial_disk_io = psutil.disk_io_counters()
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self) -> List[ResourceMetrics]:
        """Stop monitoring and return collected samples"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        
        return self.samples.copy()
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring:
            try:
                sample = self._collect_sample()
                self.samples.append(sample)
                time.sleep(self.sampling_interval)
            except Exception:
                # Ignore monitoring errors
                pass
    
    def _collect_sample(self) -> ResourceMetrics:
        """Collect single resource usage sample"""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=None)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_usage_mb = (memory.total - memory.available) / (1024 * 1024)
        memory_percent = memory.percent
        
        # Disk I/O (delta from start)
        current_disk_io = psutil.disk_io_counters()
        if current_disk_io and self._initial_disk_io:
            disk_read_mb = (current_disk_io.read_bytes - self._initial_disk_io.read_bytes) / (1024 * 1024)
            disk_write_mb = (current_disk_io.write_bytes - self._initial_disk_io.write_bytes) / (1024 * 1024)
        else:
            disk_read_mb = disk_write_mb = 0.0
        
        # Network I/O (delta from start)
        current_net_io = psutil.net_io_counters()
        if current_net_io and self._initial_net_io:
            net_sent_mb = (current_net_io.bytes_sent - self._initial_net_io.bytes_sent) / (1024 * 1024)
            net_recv_mb = (current_net_io.bytes_recv - self._initial_net_io.bytes_recv) / (1024 * 1024)
        else:
            net_sent_mb = net_recv_mb = 0.0
        
        return ResourceMetrics(
            cpu_percent=cpu_percent,
            memory_usage_mb=memory_usage_mb,
            memory_percent=memory_percent,
            disk_io_read_mb=disk_read_mb,
            disk_io_write_mb=disk_write_mb,
            network_sent_mb=net_sent_mb,
            network_recv_mb=net_recv_mb,
            timestamp=datetime.now(timezone.utc).isoformat()
        )


class WorkflowPerformanceMonitor:
    """Performance monitoring for workflow components"""
    
    PERFORMANCE_REQUIREMENTS = {
        "doc_health_scan": {"max_time": 30.0, "max_memory_mb": 256},
        "mkdocs_build": {"max_time": 60.0, "max_memory_mb": 512},
        "roadmap_lint": {"max_time": 10.0, "max_memory_mb": 128},
        "config_validation": {"max_time": 5.0, "max_memory_mb": 64},
        "test_execution": {"max_time": 300.0, "max_memory_mb": 1024}
    }
    
    def __init__(self, output_dir: str = "performance_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.system_monitor = SystemMonitor()
        self.performance_history: List[PerformanceReport] = []
    
    @contextmanager
    def measure_execution(self, component_name: str, test_scenario: str = "default"):
        """Context manager for measuring component execution"""
        # Start monitoring
        self.system_monitor.start_monitoring()
        start_time = time.time()
        
        performance_metrics = []
        
        try:
            yield performance_metrics
        finally:
            # Stop monitoring and calculate results
            execution_time = time.time() - start_time
            resource_samples = self.system_monitor.stop_monitoring()
            
            # Calculate resource metrics summary
            resource_summary = self._calculate_resource_summary(resource_samples)
            
            # Calculate statistical analysis
            statistical_analysis = self._calculate_statistical_analysis(
                execution_time, resource_samples, performance_metrics
            )
            
            # Create performance report
            report = PerformanceReport(
                component_name=component_name,
                test_scenario=test_scenario,
                execution_time=execution_time,
                resource_metrics=resource_summary,
                performance_metrics=performance_metrics,
                statistical_analysis=statistical_analysis,
                benchmark_comparison=self._compare_with_requirements(component_name, execution_time, resource_summary)
            )
            
            self.performance_history.append(report)
            
            # Save individual report
            self._save_performance_report(report)
    
    def measure_component_performance(self, 
                                    component_func: Callable, 
                                    component_name: str,
                                    test_scenarios: List[Tuple[str, List[Any]]] = None,
                                    iterations: int = 3) -> List[PerformanceReport]:
        """Measure performance of a component function across multiple scenarios"""
        
        if test_scenarios is None:
            test_scenarios = [("default", [])]
        
        reports = []
        
        for scenario_name, args in test_scenarios:
            scenario_reports = []
            
            for iteration in range(iterations):
                with self.measure_execution(component_name, f"{scenario_name}_iter_{iteration}") as metrics:
                    try:
                        start_time = time.time()
                        result = component_func(*args)
                        end_time = time.time()
                        
                        # Add custom metrics
                        metrics.append(PerformanceMetric(
                            name="function_execution_time",
                            value=end_time - start_time,
                            unit="seconds",
                            timestamp=datetime.now(timezone.utc).isoformat(),
                            metadata={"iteration": iteration, "scenario": scenario_name}
                        ))
                        
                        if hasattr(result, '__len__'):
                            metrics.append(PerformanceMetric(
                                name="output_size",
                                value=len(result),
                                unit="items",
                                timestamp=datetime.now(timezone.utc).isoformat()
                            ))
                        
                    except Exception as e:
                        metrics.append(PerformanceMetric(
                            name="error_occurred",
                            value=1.0,
                            unit="boolean",
                            timestamp=datetime.now(timezone.utc).isoformat(),
                            metadata={"error": str(e)}
                        ))
                
                if self.performance_history:
                    scenario_reports.append(self.performance_history[-1])
            
            # Calculate scenario summary
            if scenario_reports:
                scenario_summary = self._calculate_scenario_summary(scenario_reports, scenario_name)
                reports.extend(scenario_reports)
        
        return reports
    
    def benchmark_workflow_scripts(self) -> Dict[str, PerformanceReport]:
        """Benchmark all workflow scripts with realistic data"""
        benchmark_results = {}
        
        # Test documentation health validator
        doc_health_result = self._benchmark_doc_health_validator()
        if doc_health_result:
            benchmark_results["doc_health_validator"] = doc_health_result
        
        # Test MkDocs configuration validator
        mkdocs_result = self._benchmark_mkdocs_validator()
        if mkdocs_result:
            benchmark_results["mkdocs_validator"] = mkdocs_result
        
        # Test GitHub Actions integration
        github_actions_result = self._benchmark_github_actions_integration()
        if github_actions_result:
            benchmark_results["github_actions_integration"] = github_actions_result
        
        # Test production error handling
        error_handling_result = self._benchmark_error_handling()
        if error_handling_result:
            benchmark_results["production_error_handling"] = error_handling_result
        
        return benchmark_results
    
    def _benchmark_doc_health_validator(self) -> Optional[PerformanceReport]:
        """Benchmark documentation health validator"""
        script_path = "autocoder_cc/tools/ci/validate_doc_health.py"
        if not os.path.exists(script_path):
            return None
        
        # Create test health report
        test_data = {
            "health_score": 85,
            "statistics": {"high_issues": 2, "total_issues": 10},
            "coverage": {"overall": 0.85}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name
        
        try:
            with self.measure_execution("doc_health_validator", "realistic_data") as metrics:
                start_time = time.time()
                
                result = subprocess.run([
                    sys.executable, script_path, temp_file, "--summary"
                ], capture_output=True, text=True, timeout=30)
                
                execution_time = time.time() - start_time
                
                metrics.append(PerformanceMetric(
                    name="subprocess_execution_time",
                    value=execution_time,
                    unit="seconds",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    metadata={"exit_code": result.returncode, "output_length": len(result.stdout)}
                ))
                
                if result.returncode == 0:
                    try:
                        output_data = json.loads(result.stdout)
                        metrics.append(PerformanceMetric(
                            name="json_parse_success",
                            value=1.0,
                            unit="boolean",
                            timestamp=datetime.now(timezone.utc).isoformat(),
                            metadata={"output_fields": len(output_data)}
                        ))
                    except json.JSONDecodeError:
                        metrics.append(PerformanceMetric(
                            name="json_parse_success",
                            value=0.0,
                            unit="boolean",
                            timestamp=datetime.now(timezone.utc).isoformat()
                        ))
            
            return self.performance_history[-1] if self.performance_history else None
            
        finally:
            os.unlink(temp_file)
    
    def _benchmark_mkdocs_validator(self) -> Optional[PerformanceReport]:
        """Benchmark MkDocs configuration validator"""
        script_path = "autocoder_cc/tools/ci/validate_mkdocs_config.py"
        config_path = "mkdocs.yml"
        
        if not os.path.exists(script_path) or not os.path.exists(config_path):
            return None
        
        with self.measure_execution("mkdocs_validator", "real_config") as metrics:
            start_time = time.time()
            
            result = subprocess.run([
                sys.executable, script_path, config_path, "--format", "json"
            ], capture_output=True, text=True, timeout=60)
            
            execution_time = time.time() - start_time
            
            metrics.append(PerformanceMetric(
                name="validation_execution_time",
                value=execution_time,
                unit="seconds",
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata={"exit_code": result.returncode}
            ))
            
            if result.returncode in [0, 1]:  # Success or validation failure
                try:
                    output_data = json.loads(result.stdout)
                    metrics.append(PerformanceMetric(
                        name="issues_found",
                        value=output_data.get("error_count", 0) + output_data.get("warning_count", 0),
                        unit="count",
                        timestamp=datetime.now(timezone.utc).isoformat()
                    ))
                except json.JSONDecodeError:
                    pass
        
        return self.performance_history[-1] if self.performance_history else None
    
    def _benchmark_github_actions_integration(self) -> Optional[PerformanceReport]:
        """Benchmark GitHub Actions integration module"""
        script_path = "autocoder_cc/tools/ci/github_actions_integration.py"
        if not os.path.exists(script_path):
            return None
        
        with self.measure_execution("github_actions_integration", "annotation_generation") as metrics:
            start_time = time.time()
            
            result = subprocess.run([
                sys.executable, script_path
            ], capture_output=True, text=True, timeout=30)
            
            execution_time = time.time() - start_time
            
            metrics.append(PerformanceMetric(
                name="integration_execution_time",
                value=execution_time,
                unit="seconds",
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata={"exit_code": result.returncode, "output_lines": len(result.stdout.split('\n'))}
            ))
            
            # Count annotations in output
            annotation_count = result.stdout.count("::error::") + result.stdout.count("::warning::") + result.stdout.count("::notice::")
            metrics.append(PerformanceMetric(
                name="annotations_generated",
                value=annotation_count,
                unit="count",
                timestamp=datetime.now(timezone.utc).isoformat()
            ))
        
        return self.performance_history[-1] if self.performance_history else None
    
    def _benchmark_error_handling(self) -> Optional[PerformanceReport]:
        """Benchmark production error handling"""
        script_path = "autocoder_cc/tools/ci/production_validate_doc_health.py"
        if not os.path.exists(script_path):
            return None
        
        with self.measure_execution("production_error_handling", "error_scenario") as metrics:
            start_time = time.time()
            
            # Test with non-existent file to trigger error handling
            result = subprocess.run([
                sys.executable, script_path, "nonexistent_file.json"
            ], capture_output=True, text=True, timeout=30)
            
            execution_time = time.time() - start_time
            
            metrics.append(PerformanceMetric(
                name="error_handling_time",
                value=execution_time,
                unit="seconds",
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata={"exit_code": result.returncode}
            ))
            
            # Check for structured logging output
            structured_logs = 0
            github_annotations = 0
            
            for line in (result.stdout + result.stderr).split('\n'):
                if line.strip().startswith('{') and '"correlation_id"' in line:
                    structured_logs += 1
                if '::error::' in line:
                    github_annotations += 1
            
            metrics.append(PerformanceMetric(
                name="structured_log_entries",
                value=structured_logs,
                unit="count",
                timestamp=datetime.now(timezone.utc).isoformat()
            ))
            
            metrics.append(PerformanceMetric(
                name="github_error_annotations",
                value=github_annotations,
                unit="count",
                timestamp=datetime.now(timezone.utc).isoformat()
            ))
        
        return self.performance_history[-1] if self.performance_history else None
    
    def _calculate_resource_summary(self, samples: List[ResourceMetrics]) -> ResourceMetrics:
        """Calculate summary statistics for resource usage samples"""
        if not samples:
            return ResourceMetrics(
                cpu_percent=0, memory_usage_mb=0, memory_percent=0,
                disk_io_read_mb=0, disk_io_write_mb=0,
                network_sent_mb=0, network_recv_mb=0,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        
        # Calculate averages
        cpu_avg = statistics.mean(s.cpu_percent for s in samples)
        memory_avg = statistics.mean(s.memory_usage_mb for s in samples)
        memory_percent_avg = statistics.mean(s.memory_percent for s in samples)
        
        # Use maximum values for cumulative metrics
        disk_read_max = max(s.disk_io_read_mb for s in samples)
        disk_write_max = max(s.disk_io_write_mb for s in samples)
        net_sent_max = max(s.network_sent_mb for s in samples)
        net_recv_max = max(s.network_recv_mb for s in samples)
        
        return ResourceMetrics(
            cpu_percent=cpu_avg,
            memory_usage_mb=memory_avg,
            memory_percent=memory_percent_avg,
            disk_io_read_mb=disk_read_max,
            disk_io_write_mb=disk_write_max,
            network_sent_mb=net_sent_max,
            network_recv_mb=net_recv_max,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    def _calculate_statistical_analysis(self, 
                                      execution_time: float, 
                                      resource_samples: List[ResourceMetrics],
                                      performance_metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Calculate statistical analysis of performance data"""
        analysis = {
            "execution_time": execution_time,
            "sample_count": len(resource_samples),
            "sampling_duration": execution_time
        }
        
        if resource_samples:
            cpu_values = [s.cpu_percent for s in resource_samples]
            memory_values = [s.memory_usage_mb for s in resource_samples]
            
            analysis.update({
                "cpu_statistics": {
                    "mean": statistics.mean(cpu_values),
                    "median": statistics.median(cpu_values),
                    "max": max(cpu_values),
                    "min": min(cpu_values),
                    "stdev": statistics.stdev(cpu_values) if len(cpu_values) > 1 else 0
                },
                "memory_statistics": {
                    "mean_mb": statistics.mean(memory_values),
                    "median_mb": statistics.median(memory_values),
                    "max_mb": max(memory_values),
                    "min_mb": min(memory_values),
                    "stdev_mb": statistics.stdev(memory_values) if len(memory_values) > 1 else 0
                }
            })
        
        # Analyze custom performance metrics
        metric_analysis = {}
        for metric in performance_metrics:
            if metric.name not in metric_analysis:
                metric_analysis[metric.name] = []
            metric_analysis[metric.name].append(metric.value)
        
        for metric_name, values in metric_analysis.items():
            if len(values) > 0:
                analysis[f"{metric_name}_statistics"] = {
                    "count": len(values),
                    "sum": sum(values),
                    "mean": statistics.mean(values),
                    "max": max(values),
                    "min": min(values)
                }
                if len(values) > 1:
                    analysis[f"{metric_name}_statistics"]["stdev"] = statistics.stdev(values)
        
        return analysis
    
    def _compare_with_requirements(self, 
                                 component_name: str, 
                                 execution_time: float, 
                                 resource_metrics: ResourceMetrics) -> Dict[str, Any]:
        """Compare performance against requirements"""
        requirements = self.PERFORMANCE_REQUIREMENTS.get(component_name, {})
        if not requirements:
            return None
        
        comparison = {
            "requirements_met": True,
            "violations": []
        }
        
        # Check execution time
        if "max_time" in requirements:
            max_time = requirements["max_time"]
            if execution_time > max_time:
                comparison["requirements_met"] = False
                comparison["violations"].append({
                    "metric": "execution_time",
                    "required": f"<= {max_time}s",
                    "actual": f"{execution_time:.2f}s",
                    "violation_factor": execution_time / max_time
                })
        
        # Check memory usage
        if "max_memory_mb" in requirements:
            max_memory = requirements["max_memory_mb"]
            if resource_metrics.memory_usage_mb > max_memory:
                comparison["requirements_met"] = False
                comparison["violations"].append({
                    "metric": "memory_usage",
                    "required": f"<= {max_memory}MB",
                    "actual": f"{resource_metrics.memory_usage_mb:.2f}MB",
                    "violation_factor": resource_metrics.memory_usage_mb / max_memory
                })
        
        return comparison
    
    def _calculate_scenario_summary(self, reports: List[PerformanceReport], scenario_name: str):
        """Calculate summary statistics across multiple iterations"""
        execution_times = [r.execution_time for r in reports]
        
        summary = {
            "scenario": scenario_name,
            "iterations": len(reports),
            "execution_time_statistics": {
                "mean": statistics.mean(execution_times),
                "median": statistics.median(execution_times),
                "min": min(execution_times),
                "max": max(execution_times),
                "stdev": statistics.stdev(execution_times) if len(execution_times) > 1 else 0
            }
        }
        
        # Save scenario summary
        summary_file = self.output_dir / f"scenario_summary_{scenario_name}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary
    
    def _save_performance_report(self, report: PerformanceReport):
        """Save individual performance report"""
        filename = f"performance_{report.component_name}_{report.test_scenario}_{int(time.time())}.json"
        report_file = self.output_dir / filename
        
        with open(report_file, 'w') as f:
            json.dump(asdict(report), f, indent=2, default=str)
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance analysis report"""
        if not self.performance_history:
            return {"error": "No performance data collected"}
        
        # Group reports by component
        components = {}
        for report in self.performance_history:
            if report.component_name not in components:
                components[report.component_name] = []
            components[report.component_name].append(report)
        
        # Calculate overall statistics
        all_execution_times = [r.execution_time for r in self.performance_history]
        
        comprehensive_report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_reports": len(self.performance_history),
            "components_tested": len(components),
            "overall_statistics": {
                "mean_execution_time": statistics.mean(all_execution_times),
                "median_execution_time": statistics.median(all_execution_times),
                "max_execution_time": max(all_execution_times),
                "min_execution_time": min(all_execution_times),
                "total_execution_time": sum(all_execution_times)
            },
            "component_summaries": {}
        }
        
        # Component-specific summaries
        for component_name, reports in components.items():
            component_times = [r.execution_time for r in reports]
            requirements_met = all(
                not r.benchmark_comparison or r.benchmark_comparison.get("requirements_met", True)
                for r in reports
            )
            
            comprehensive_report["component_summaries"][component_name] = {
                "test_count": len(reports),
                "mean_execution_time": statistics.mean(component_times),
                "requirements_met": requirements_met,
                "performance_trend": "stable",  # Could be enhanced with trend analysis
                "latest_report": asdict(reports[-1])
            }
        
        # Save comprehensive report
        report_file = self.output_dir / "comprehensive_performance_report.json"
        with open(report_file, 'w') as f:
            json.dump(comprehensive_report, f, indent=2, default=str)
        
        return comprehensive_report


def main():
    """CLI interface for performance monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Performance monitoring and benchmarking')
    parser.add_argument('--component', help='Specific component to benchmark')
    parser.add_argument('--benchmark-all', action='store_true', 
                       help='Benchmark all workflow components')
    parser.add_argument('--output-dir', default='performance_results',
                       help='Output directory for results')
    parser.add_argument('--iterations', type=int, default=3,
                       help='Number of test iterations')
    
    args = parser.parse_args()
    
    print("⚡ Starting performance monitoring...")
    print(f"📁 Output directory: {args.output_dir}")
    
    monitor = WorkflowPerformanceMonitor(args.output_dir)
    
    try:
        if args.benchmark_all:
            print("🔍 Benchmarking all workflow components...")
            results = monitor.benchmark_workflow_scripts()
            
            print(f"\n✅ Benchmarking completed!")
            print(f"📊 Components tested: {len(results)}")
            
            for component, report in results.items():
                print(f"  - {component}: {report.execution_time:.2f}s")
                if report.benchmark_comparison:
                    requirements_met = report.benchmark_comparison.get("requirements_met", True)
                    print(f"    Requirements met: {'✅' if requirements_met else '❌'}")
        
        # Generate comprehensive report
        comprehensive_report = monitor.generate_comprehensive_report()
        
        if "error" not in comprehensive_report:
            print(f"\n📋 Performance Summary:")
            print(f"  - Total tests: {comprehensive_report['total_reports']}")
            print(f"  - Components: {comprehensive_report['components_tested']}")
            print(f"  - Mean execution time: {comprehensive_report['overall_statistics']['mean_execution_time']:.2f}s")
            print(f"  - Total execution time: {comprehensive_report['overall_statistics']['total_execution_time']:.2f}s")
            
            print(f"\n📝 Comprehensive report: {args.output_dir}/comprehensive_performance_report.json")
        
    except KeyboardInterrupt:
        print("\n❌ Performance monitoring interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Performance monitoring failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()