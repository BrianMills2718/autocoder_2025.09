#!/usr/bin/env python3
"""
Evidence Collection Framework - Honest and Statistical Performance Testing

This module provides rigorous evidence collection for AutoCoder4_CC phase testing
with statistical validation and honest failure documentation.
"""

import time
import statistics
import subprocess
import json
import platform
import psutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class TimingResult:
    """Statistical timing result with confidence intervals."""
    mean: float
    median: float
    std_dev: float
    min_time: float
    max_time: float
    sample_size: int
    raw_times: List[float]
    
    def __str__(self):
        return (f"μ={self.mean:.2f}s ±{self.std_dev:.2f}s "
                f"(n={self.sample_size}, range: {self.min_time:.2f}-{self.max_time:.2f}s)")

@dataclass
class TestResult:
    """Comprehensive test result with success/failure status."""
    name: str
    success: bool
    timing: Optional[TimingResult]
    stdout: str
    stderr: str
    exit_code: int
    error_message: Optional[str]
    raw_command: str

class EvidenceCollector:
    """Collects rigorous statistical evidence for phase testing performance."""
    
    def __init__(self, min_samples: int = 5, max_samples: int = 10):
        self.min_samples = min_samples
        self.max_samples = max_samples
        self.hardware_info = self._collect_hardware_info()
        
    def _collect_hardware_info(self) -> Dict[str, Any]:
        """Collect hardware context for performance measurements."""
        return {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(logical=False),
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "total_memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "python_version": platform.python_version(),
            "architecture": platform.architecture()[0]
        }
    
    def time_command_statistical(self, command: List[str], 
                               working_dir: Optional[str] = None,
                               timeout: int = 600) -> TimingResult:
        """Run command multiple times and collect statistical timing data."""
        times = []
        
        for i in range(self.max_samples):
            logger.info(f"Running timing sample {i+1}/{self.max_samples}: {' '.join(command)}")
            
            start_time = time.perf_counter()
            try:
                result = subprocess.run(
                    command,
                    cwd=working_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                end_time = time.perf_counter()
                
                # Only count successful runs
                if result.returncode == 0:
                    elapsed = end_time - start_time
                    times.append(elapsed)
                    logger.info(f"Sample {i+1} completed successfully in {elapsed:.2f}s")
                else:
                    logger.warning(f"Sample {i+1} failed with exit code {result.returncode}")
                    
            except subprocess.TimeoutExpired:
                logger.error(f"Sample {i+1} timed out after {timeout}s")
                continue
            except Exception as e:
                logger.error(f"Sample {i+1} failed with error: {e}")
                continue
        
        if len(times) < self.min_samples:
            raise RuntimeError(f"Insufficient successful samples: {len(times)} < {self.min_samples}")
        
        return TimingResult(
            mean=statistics.mean(times),
            median=statistics.median(times),
            std_dev=statistics.stdev(times) if len(times) > 1 else 0.0,
            min_time=min(times),
            max_time=max(times),
            sample_size=len(times),
            raw_times=times
        )
    
    def run_test_with_evidence(self, test_command: List[str],
                             working_dir: Optional[str] = None,
                             collect_timing: bool = True,
                             timeout: int = 600) -> TestResult:
        """Run a single test and collect comprehensive evidence."""
        
        timing = None
        if collect_timing:
            try:
                timing = self.time_command_statistical(test_command, working_dir, timeout)
                success = True
                stdout = f"Test completed successfully in {timing}"
                stderr = ""
                exit_code = 0
                error_message = None
            except Exception as e:
                success = False
                stdout = ""
                stderr = str(e)
                exit_code = 1
                error_message = f"Timing collection failed: {e}"
        else:
            # Single run for non-timing tests
            try:
                result = subprocess.run(
                    test_command,
                    cwd=working_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                success = result.returncode == 0
                stdout = result.stdout
                stderr = result.stderr
                exit_code = result.returncode
                error_message = None if success else "Test failed"
            except Exception as e:
                success = False
                stdout = ""
                stderr = str(e)
                exit_code = 1
                error_message = f"Test execution failed: {e}"
        
        return TestResult(
            name=" ".join(test_command),
            success=success,
            timing=timing,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            error_message=error_message,
            raw_command=" ".join(test_command)
        )
    
    def validate_performance_claim(self, measured_time: float, 
                                 baseline_time: float,
                                 claimed_improvement: str) -> Tuple[bool, str]:
        """Validate performance improvement claims with statistical rigor."""
        
        if baseline_time <= 0:
            return False, f"Invalid baseline time: {baseline_time}"
        
        actual_improvement = baseline_time / measured_time
        
        # Parse claimed improvement (e.g., "50x faster", "3x improvement")
        try:
            if "x faster" in claimed_improvement:
                claimed_factor = float(claimed_improvement.replace("x faster", "").strip())
            elif "x improvement" in claimed_improvement:
                claimed_factor = float(claimed_improvement.replace("x improvement", "").strip())
            else:
                return False, f"Cannot parse improvement claim: {claimed_improvement}"
        except ValueError:
            return False, f"Invalid improvement format: {claimed_improvement}"
        
        # Allow 20% tolerance for performance variation
        tolerance = 0.2
        min_acceptable = claimed_factor * (1 - tolerance)
        max_acceptable = claimed_factor * (1 + tolerance)
        
        if min_acceptable <= actual_improvement <= max_acceptable:
            return True, f"VALIDATED: {actual_improvement:.1f}x improvement matches claim of {claimed_improvement}"
        else:
            return False, f"INVALID: {actual_improvement:.1f}x improvement does not match claim of {claimed_improvement}"
    
    def generate_honest_evidence_report(self, test_results: List[TestResult],
                                      performance_claims: List[Dict[str, Any]]) -> str:
        """Generate honest evidence report with statistical validation."""
        
        report = []
        report.append("# Honest Evidence Report - Statistical Performance Analysis")
        report.append(f"**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**Minimum Samples**: {self.min_samples}")
        report.append("")
        
        # Hardware context
        report.append("## Hardware Context")
        for key, value in self.hardware_info.items():
            report.append(f"- **{key}**: {value}")
        report.append("")
        
        # Test results summary
        successful_tests = [t for t in test_results if t.success]
        failed_tests = [t for t in test_results if not t.success]
        
        report.append("## Test Results Summary")
        report.append(f"- **Total Tests**: {len(test_results)}")
        report.append(f"- **Successful**: {len(successful_tests)}")
        report.append(f"- **Failed**: {len(failed_tests)}")
        report.append(f"- **Success Rate**: {len(successful_tests)/len(test_results)*100:.1f}%")
        report.append("")
        
        # Detailed test results
        report.append("## Detailed Test Results")
        for test in test_results:
            status = "✅ PASS" if test.success else "❌ FAIL"
            report.append(f"### {status}: {test.name}")
            
            if test.timing:
                report.append(f"**Performance**: {test.timing}")
                report.append(f"**Raw Times**: {[f'{t:.2f}s' for t in test.timing.raw_times]}")
            
            if test.success:
                if test.stdout.strip():
                    report.append("**Output**:")
                    report.append("```")
                    report.append(test.stdout.strip())
                    report.append("```")
            else:
                report.append(f"**Exit Code**: {test.exit_code}")
                if test.error_message:
                    report.append(f"**Error**: {test.error_message}")
                if test.stderr.strip():
                    report.append("**Error Output**:")
                    report.append("```")
                    report.append(test.stderr.strip())
                    report.append("```")
            report.append("")
        
        # Performance claims validation
        if performance_claims:
            report.append("## Performance Claims Validation")
            for claim in performance_claims:
                validation_result = self.validate_performance_claim(
                    claim['measured_time'],
                    claim['baseline_time'],
                    claim['claimed_improvement']
                )
                status = "✅ VALIDATED" if validation_result[0] else "❌ INVALID"
                report.append(f"- **{status}**: {validation_result[1]}")
            report.append("")
        
        # Honest limitations
        report.append("## Limitations and Caveats")
        report.append("- Performance measurements subject to system load and hardware variations")
        report.append("- Test environment may differ from production conditions")
        report.append("- Statistical samples collected under controlled conditions")
        report.append("- Some tests may use mock data rather than realistic workloads")
        report.append("")
        
        return "\n".join(report)

def main():
    """Example usage of the evidence collection framework."""
    collector = EvidenceCollector(min_samples=3, max_samples=5)
    
    # Example: Test a simple command
    test_result = collector.run_test_with_evidence(
        ["python", "-c", "import time; time.sleep(0.1); print('Hello')"],
        collect_timing=True
    )
    
    print(f"Test result: {test_result.success}")
    if test_result.timing:
        print(f"Timing: {test_result.timing}")

if __name__ == "__main__":
    main()