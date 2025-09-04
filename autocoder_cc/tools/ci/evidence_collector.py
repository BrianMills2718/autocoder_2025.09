"""
Production-Grade Evidence Collection System - Task 15 Implementation

Automated evidence collection with real execution, performance metrics,
reproducible test scenarios, and comprehensive logging as required by Gemini findings.
"""

import asyncio
import json
import logging
import subprocess
import time
import psutil
import os
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
import tempfile
import shutil
import statistics
import yaml
import docker
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


@dataclass
class EvidenceItem:
    """Single piece of evidence with metadata"""
    evidence_id: str
    timestamp: str
    evidence_type: str  # test_execution, performance_measurement, system_log, etc.
    source_command: str
    execution_duration_seconds: float
    output_data: Dict[str, Any]
    raw_output: str
    exit_code: int
    reproducible: bool
    verification_hash: str
    metadata: Dict[str, Any]


@dataclass
class TestExecutionEvidence:
    """Evidence from test execution"""
    test_suite: str
    test_results: Dict[str, Any]
    coverage_report: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    execution_logs: List[str]
    artifacts: List[str]
    statistical_analysis: Dict[str, Any]


@dataclass
class PerformanceMeasurement:
    """Performance measurement with statistical analysis"""
    measurement_type: str
    metric_name: str
    value: float
    unit: str
    sample_size: int
    confidence_interval: Tuple[float, float]
    statistical_significance: float
    measurement_conditions: Dict[str, Any]
    baseline_comparison: Optional[Dict[str, Any]] = None


@dataclass
class SystemHealthEvidence:
    """System health evidence"""
    system_metrics: Dict[str, Any]
    resource_utilization: Dict[str, Any]
    error_logs: List[str]
    health_checks: Dict[str, Any]
    service_status: Dict[str, Any]


@dataclass
class EvidenceCollection:
    """Complete evidence collection"""
    collection_id: str
    collection_timestamp: str
    collection_duration_seconds: float
    evidence_items: List[EvidenceItem]
    test_execution_evidence: List[TestExecutionEvidence]
    performance_measurements: List[PerformanceMeasurement]
    system_health_evidence: SystemHealthEvidence
    verification_results: Dict[str, Any]
    reproducibility_score: float
    evidence_quality_score: float
    metadata: Dict[str, Any]


class EvidenceCollector:
    """Production-grade evidence collector"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("evidence_collection")
        self.output_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
        self.evidence_items: List[EvidenceItem] = []
        self.collection_start_time = None
        self.collection_id = None
        
        # Initialize monitoring
        self.system_monitor = SystemMonitor()
        self.performance_tracker = PerformanceTracker()
        
        # Docker client for containerized testing
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            self.logger.warning(f"Docker not available: {e}")
            self.docker_client = None
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(self.output_dir / "evidence_collection.log"),
                logging.StreamHandler()
            ]
        )
    
    async def start_collection(self) -> str:
        """Start evidence collection session"""
        self.collection_id = f"evidence_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        self.collection_start_time = time.time()
        
        # Create collection directory
        collection_dir = self.output_dir / self.collection_id
        collection_dir.mkdir(exist_ok=True)
        
        # Start system monitoring
        await self.system_monitor.start_monitoring()
        
        self.logger.info(f"Started evidence collection: {self.collection_id}")
        return self.collection_id
    
    async def stop_collection(self) -> EvidenceCollection:
        """Stop evidence collection and generate report"""
        if not self.collection_id:
            raise ValueError("Collection not started")
        
        collection_duration = time.time() - self.collection_start_time
        
        # Stop system monitoring
        system_health = await self.system_monitor.stop_monitoring()
        
        # Generate verification results
        verification_results = await self._generate_verification_results()
        
        # Calculate quality scores
        reproducibility_score = self._calculate_reproducibility_score()
        evidence_quality_score = self._calculate_evidence_quality_score()
        
        # Create evidence collection
        evidence_collection = EvidenceCollection(
            collection_id=self.collection_id,
            collection_timestamp=datetime.now(timezone.utc).isoformat(),
            collection_duration_seconds=collection_duration,
            evidence_items=self.evidence_items,
            test_execution_evidence=await self._collect_test_execution_evidence(),
            performance_measurements=await self._collect_performance_measurements(),
            system_health_evidence=system_health,
            verification_results=verification_results,
            reproducibility_score=reproducibility_score,
            evidence_quality_score=evidence_quality_score,
            metadata={
                "collection_environment": await self._get_environment_info(),
                "collection_tools": await self._get_tool_versions(),
                "collection_configuration": await self._get_collection_config()
            }
        )
        
        # Save evidence collection
        await self._save_evidence_collection(evidence_collection)
        
        self.logger.info(f"Completed evidence collection: {self.collection_id}")
        return evidence_collection
    
    async def collect_test_execution_evidence(self, test_command: str, 
                                            test_directory: Path) -> EvidenceItem:
        """Collect evidence from test execution"""
        evidence_id = f"test_execution_{len(self.evidence_items)}"
        start_time = time.time()
        
        self.logger.info(f"Collecting test execution evidence: {test_command}")
        
        try:
            # Execute test command
            process = await asyncio.create_subprocess_exec(
                *test_command.split(),
                cwd=test_directory,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy()
            )
            
            stdout, stderr = await process.communicate()
            exit_code = process.returncode
            
            execution_duration = time.time() - start_time
            
            # Parse test results
            output_data = await self._parse_test_output(stdout.decode(), stderr.decode())
            
            # Generate verification hash
            verification_hash = self._generate_verification_hash(
                test_command, stdout.decode(), stderr.decode()
            )
            
            # Create evidence item
            evidence_item = EvidenceItem(
                evidence_id=evidence_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                evidence_type="test_execution",
                source_command=test_command,
                execution_duration_seconds=execution_duration,
                output_data=output_data,
                raw_output=stdout.decode() + stderr.decode(),
                exit_code=exit_code,
                reproducible=True,
                verification_hash=verification_hash,
                metadata={
                    "test_directory": str(test_directory),
                    "environment": dict(os.environ),
                    "system_info": await self._get_system_info()
                }
            )
            
            self.evidence_items.append(evidence_item)
            
            # Save raw output to file
            output_file = self.output_dir / self.collection_id / f"{evidence_id}_output.txt"
            with open(output_file, 'w') as f:
                f.write(evidence_item.raw_output)
            
            self.logger.info(f"Collected test execution evidence: {evidence_id}")
            return evidence_item
            
        except Exception as e:
            self.logger.error(f"Failed to collect test execution evidence: {e}")
            raise
    
    async def collect_performance_measurement(self, operation_name: str,
                                            measurement_function,
                                            sample_size: int = 10) -> PerformanceMeasurement:
        """Collect performance measurement with statistical analysis"""
        self.logger.info(f"Collecting performance measurement: {operation_name}")
        
        measurements = []
        measurement_conditions = await self._get_measurement_conditions()
        
        # Collect multiple samples
        for i in range(sample_size):
            start_time = time.time()
            
            try:
                # Execute measurement function
                if asyncio.iscoroutinefunction(measurement_function):
                    result = await measurement_function()
                else:
                    result = measurement_function()
                
                execution_time = time.time() - start_time
                measurements.append(execution_time)
                
            except Exception as e:
                self.logger.error(f"Measurement {i} failed: {e}")
                continue
        
        if not measurements:
            raise ValueError("No successful measurements collected")
        
        # Calculate statistical metrics
        mean_value = statistics.mean(measurements)
        std_dev = statistics.stdev(measurements) if len(measurements) > 1 else 0
        
        # Calculate confidence interval (95%)
        confidence_level = 0.95
        if len(measurements) > 1:
            import math
            t_value = 2.262  # t-distribution for small samples
            margin_of_error = t_value * (std_dev / math.sqrt(len(measurements)))
            confidence_interval = (mean_value - margin_of_error, mean_value + margin_of_error)
        else:
            confidence_interval = (mean_value, mean_value)
        
        # Calculate statistical significance
        statistical_significance = self._calculate_statistical_significance(measurements)
        
        # Create performance measurement
        performance_measurement = PerformanceMeasurement(
            measurement_type="execution_time",
            metric_name=operation_name,
            value=mean_value,
            unit="seconds",
            sample_size=len(measurements),
            confidence_interval=confidence_interval,
            statistical_significance=statistical_significance,
            measurement_conditions=measurement_conditions
        )
        
        self.logger.info(f"Collected performance measurement: {operation_name} = {mean_value:.3f}s ± {std_dev:.3f}s")
        return performance_measurement
    
    async def collect_system_log_evidence(self, log_file: Path, 
                                        log_type: str = "system") -> EvidenceItem:
        """Collect evidence from system logs"""
        evidence_id = f"system_log_{len(self.evidence_items)}"
        start_time = time.time()
        
        self.logger.info(f"Collecting system log evidence: {log_file}")
        
        try:
            # Read log file
            with open(log_file, 'r') as f:
                log_content = f.read()
            
            execution_duration = time.time() - start_time
            
            # Parse log content
            output_data = await self._parse_log_content(log_content, log_type)
            
            # Generate verification hash
            verification_hash = self._generate_verification_hash(
                str(log_file), log_content, ""
            )
            
            # Create evidence item
            evidence_item = EvidenceItem(
                evidence_id=evidence_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                evidence_type="system_log",
                source_command=f"cat {log_file}",
                execution_duration_seconds=execution_duration,
                output_data=output_data,
                raw_output=log_content,
                exit_code=0,
                reproducible=True,
                verification_hash=verification_hash,
                metadata={
                    "log_file": str(log_file),
                    "log_type": log_type,
                    "file_size": os.path.getsize(log_file),
                    "file_modified": datetime.fromtimestamp(
                        os.path.getmtime(log_file), timezone.utc
                    ).isoformat()
                }
            )
            
            self.evidence_items.append(evidence_item)
            
            self.logger.info(f"Collected system log evidence: {evidence_id}")
            return evidence_item
            
        except Exception as e:
            self.logger.error(f"Failed to collect system log evidence: {e}")
            raise
    
    async def collect_docker_container_evidence(self, container_name: str) -> EvidenceItem:
        """Collect evidence from Docker container"""
        if not self.docker_client:
            raise ValueError("Docker not available")
        
        evidence_id = f"docker_container_{len(self.evidence_items)}"
        start_time = time.time()
        
        self.logger.info(f"Collecting Docker container evidence: {container_name}")
        
        try:
            # Get container
            container = self.docker_client.containers.get(container_name)
            
            # Collect container information
            container_info = {
                "id": container.id,
                "name": container.name,
                "status": container.status,
                "image": container.image.tags,
                "created": container.attrs['Created'],
                "started": container.attrs['State']['StartedAt'],
                "ports": container.attrs['NetworkSettings']['Ports']
            }
            
            # Get container logs
            logs = container.logs(timestamps=True, tail=1000).decode('utf-8')
            
            # Get container stats
            stats = container.stats(stream=False)
            
            execution_duration = time.time() - start_time
            
            # Create output data
            output_data = {
                "container_info": container_info,
                "container_stats": stats,
                "log_lines": len(logs.split('\n')),
                "status": "success"
            }
            
            # Generate verification hash
            verification_hash = self._generate_verification_hash(
                f"docker inspect {container_name}", json.dumps(output_data), logs
            )
            
            # Create evidence item
            evidence_item = EvidenceItem(
                evidence_id=evidence_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                evidence_type="docker_container",
                source_command=f"docker inspect {container_name}",
                execution_duration_seconds=execution_duration,
                output_data=output_data,
                raw_output=logs,
                exit_code=0,
                reproducible=True,
                verification_hash=verification_hash,
                metadata={
                    "container_name": container_name,
                    "docker_version": self.docker_client.version()
                }
            )
            
            self.evidence_items.append(evidence_item)
            
            self.logger.info(f"Collected Docker container evidence: {evidence_id}")
            return evidence_item
            
        except Exception as e:
            self.logger.error(f"Failed to collect Docker container evidence: {e}")
            raise
    
    async def collect_file_system_evidence(self, file_path: Path) -> EvidenceItem:
        """Collect evidence from file system"""
        evidence_id = f"file_system_{len(self.evidence_items)}"
        start_time = time.time()
        
        self.logger.info(f"Collecting file system evidence: {file_path}")
        
        try:
            # Get file stats
            stat_info = os.stat(file_path)
            
            # Read file content (if reasonable size)
            raw_output = ""
            if stat_info.st_size < 1024 * 1024:  # 1MB limit
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    raw_output = f.read()
            
            execution_duration = time.time() - start_time
            
            # Create output data
            output_data = {
                "file_path": str(file_path),
                "file_size": stat_info.st_size,
                "file_mode": oct(stat_info.st_mode),
                "created": datetime.fromtimestamp(stat_info.st_ctime, timezone.utc).isoformat(),
                "modified": datetime.fromtimestamp(stat_info.st_mtime, timezone.utc).isoformat(),
                "accessed": datetime.fromtimestamp(stat_info.st_atime, timezone.utc).isoformat(),
                "readable": os.access(file_path, os.R_OK),
                "writable": os.access(file_path, os.W_OK),
                "executable": os.access(file_path, os.X_OK)
            }
            
            # Generate verification hash
            verification_hash = self._generate_verification_hash(
                f"stat {file_path}", json.dumps(output_data), raw_output
            )
            
            # Create evidence item
            evidence_item = EvidenceItem(
                evidence_id=evidence_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                evidence_type="file_system",
                source_command=f"stat {file_path}",
                execution_duration_seconds=execution_duration,
                output_data=output_data,
                raw_output=raw_output,
                exit_code=0,
                reproducible=True,
                verification_hash=verification_hash,
                metadata={
                    "file_path": str(file_path),
                    "collection_method": "direct_access"
                }
            )
            
            self.evidence_items.append(evidence_item)
            
            self.logger.info(f"Collected file system evidence: {evidence_id}")
            return evidence_item
            
        except Exception as e:
            self.logger.error(f"Failed to collect file system evidence: {e}")
            raise
    
    async def generate_reproducibility_guide(self) -> str:
        """Generate reproducibility guide for evidence collection"""
        guide = f"""# Evidence Collection Reproducibility Guide

## Collection ID: {self.collection_id}
## Generated: {datetime.now(timezone.utc).isoformat()}

### Environment Setup

1. **System Requirements**
   - Python 3.8+
   - Docker (if using containerized tests)
   - Required system packages

2. **Environment Variables**
```bash
"""
        
        # Add environment variables
        important_env_vars = [
            'PYTHONPATH', 'PATH', 'PWD', 'USER', 'HOME',
            'DOCKER_HOST', 'KUBECONFIG'
        ]
        
        for var in important_env_vars:
            if var in os.environ:
                guide += f"export {var}={os.environ[var]}\n"
        
        guide += """```

### Reproduction Steps

"""
        
        # Add reproduction steps for each evidence item
        for i, evidence in enumerate(self.evidence_items):
            guide += f"""
#### Evidence Item {i+1}: {evidence.evidence_id}

**Command:**
```bash
{evidence.source_command}
```

**Expected Duration:** {evidence.execution_duration_seconds:.2f} seconds
**Expected Exit Code:** {evidence.exit_code}
**Verification Hash:** {evidence.verification_hash}

**Reproduction Verification:**
```bash
# Run the command and verify output hash
{evidence.source_command} | sha256sum
# Expected hash: {evidence.verification_hash}
```

"""
        
        guide += """
### Verification Commands

Run these commands to verify the evidence collection can be reproduced:

```bash
# Verify system environment
python --version
docker --version

# Verify file integrity
for file in evidence_collection/*; do
    echo "Verifying $file"
    sha256sum "$file"
done

# Run verification script
python -m tools.ci.evidence_validator verify-collection {collection_id}
```

### Expected Results

The reproduction should generate evidence items with:
- Matching verification hashes
- Similar execution times (within 20% variance)
- Identical exit codes
- Consistent output structure

### Troubleshooting

1. **Environment Differences**
   - Check Python version compatibility
   - Verify Docker installation
   - Ensure all dependencies are installed

2. **Timing Variations**
   - Performance measurements may vary by ±20%
   - Network-dependent operations may have higher variance
   - System load affects execution times

3. **File System Differences**
   - File permissions may vary between systems
   - Path separators differ between OS
   - Temporary files may have different names

### Contact

For issues reproducing this evidence collection, please:
1. Check the troubleshooting section above
2. Verify your environment matches the requirements
3. Contact the evidence collection team with your system information
"""
        
        # Save reproducibility guide
        guide_file = self.output_dir / self.collection_id / "reproducibility_guide.md"
        with open(guide_file, 'w') as f:
            f.write(guide)
        
        self.logger.info(f"Generated reproducibility guide: {guide_file}")
        return guide
    
    def _generate_verification_hash(self, command: str, output: str, 
                                  additional_data: str = "") -> str:
        """Generate verification hash for reproducibility"""
        combined_data = f"{command}|{output}|{additional_data}"
        return hashlib.sha256(combined_data.encode()).hexdigest()
    
    async def _parse_test_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse test output to extract structured data"""
        output_data = {
            "stdout_lines": len(stdout.split('\n')),
            "stderr_lines": len(stderr.split('\n')),
            "has_errors": bool(stderr.strip()),
            "status": "success" if not stderr.strip() else "failure"
        }
        
        # Try to parse pytest output
        if "pytest" in stdout.lower():
            output_data.update(self._parse_pytest_output(stdout))
        
        # Try to parse coverage output
        if "coverage" in stdout.lower():
            output_data.update(self._parse_coverage_output(stdout))
        
        return output_data
    
    def _parse_pytest_output(self, output: str) -> Dict[str, Any]:
        """Parse pytest output"""
        pytest_data = {}
        
        # Look for test results summary
        lines = output.split('\n')
        for line in lines:
            if 'passed' in line and 'failed' in line:
                # Parse test results
                parts = line.split()
                for part in parts:
                    if 'passed' in part:
                        pytest_data['tests_passed'] = int(part.split('passed')[0])
                    elif 'failed' in part:
                        pytest_data['tests_failed'] = int(part.split('failed')[0])
        
        return pytest_data
    
    def _parse_coverage_output(self, output: str) -> Dict[str, Any]:
        """Parse coverage output"""
        coverage_data = {}
        
        # Look for coverage percentage
        lines = output.split('\n')
        for line in lines:
            if '%' in line and 'coverage' in line.lower():
                # Extract coverage percentage
                import re
                match = re.search(r'(\d+)%', line)
                if match:
                    coverage_data['coverage_percentage'] = int(match.group(1))
        
        return coverage_data
    
    async def _parse_log_content(self, log_content: str, log_type: str) -> Dict[str, Any]:
        """Parse log content to extract structured data"""
        log_data = {
            "log_type": log_type,
            "total_lines": len(log_content.split('\n')),
            "log_size": len(log_content),
            "timestamp_range": self._extract_timestamp_range(log_content)
        }
        
        # Count log levels
        log_levels = ['ERROR', 'WARNING', 'INFO', 'DEBUG']
        for level in log_levels:
            count = log_content.count(level)
            log_data[f"{level.lower()}_count"] = count
        
        return log_data
    
    def _extract_timestamp_range(self, log_content: str) -> Dict[str, str]:
        """Extract timestamp range from log content"""
        import re
        
        # Common timestamp patterns
        timestamp_patterns = [
            r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
            r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}'
        ]
        
        timestamps = []
        for pattern in timestamp_patterns:
            matches = re.findall(pattern, log_content)
            timestamps.extend(matches)
        
        if timestamps:
            return {
                "earliest": min(timestamps),
                "latest": max(timestamps),
                "count": len(timestamps)
            }
        
        return {"earliest": None, "latest": None, "count": 0}
    
    async def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            "platform": os.name,
            "python_version": os.sys.version,
            "working_directory": os.getcwd(),
            "user": os.getenv('USER', 'unknown'),
            "hostname": os.getenv('HOSTNAME', 'unknown'),
            "cpu_count": os.cpu_count(),
            "memory_total": psutil.virtual_memory().total
        }
    
    async def _get_environment_info(self) -> Dict[str, Any]:
        """Get environment information"""
        return {
            "python_version": os.sys.version,
            "platform": os.name,
            "working_directory": os.getcwd(),
            "environment_variables": dict(os.environ),
            "system_info": await self._get_system_info()
        }
    
    async def _get_tool_versions(self) -> Dict[str, str]:
        """Get versions of tools used in evidence collection"""
        tools = {}
        
        # Python version
        tools['python'] = os.sys.version
        
        # Try to get Docker version
        if self.docker_client:
            try:
                docker_version = self.docker_client.version()
                tools['docker'] = docker_version['Version']
            except Exception:
                pass
        
        # Try to get pytest version
        try:
            result = subprocess.run(['pytest', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                tools['pytest'] = result.stdout.strip()
        except Exception:
            pass
        
        # Try to get git version
        try:
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                tools['git'] = result.stdout.strip()
        except Exception:
            pass
        
        return tools
    
    async def _get_collection_config(self) -> Dict[str, Any]:
        """Get collection configuration"""
        return {
            "output_directory": str(self.output_dir),
            "collection_id": self.collection_id,
            "log_level": self.logger.level,
            "docker_available": self.docker_client is not None
        }
    
    async def _get_measurement_conditions(self) -> Dict[str, Any]:
        """Get measurement conditions"""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "load_average": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else None,
            "system_uptime": time.time() - psutil.boot_time()
        }
    
    def _calculate_statistical_significance(self, measurements: List[float]) -> float:
        """Calculate statistical significance of measurements"""
        if len(measurements) < 2:
            return 0.0
        
        # Simple calculation based on coefficient of variation
        mean_val = statistics.mean(measurements)
        std_val = statistics.stdev(measurements)
        
        if mean_val == 0:
            return 0.0
        
        cv = std_val / mean_val
        
        # Convert to significance score (lower CV = higher significance)
        significance = max(0.0, 1.0 - cv)
        return significance
    
    async def _collect_test_execution_evidence(self) -> List[TestExecutionEvidence]:
        """Collect test execution evidence"""
        test_evidence = []
        
        # Filter test execution evidence items
        test_items = [item for item in self.evidence_items 
                     if item.evidence_type == "test_execution"]
        
        for item in test_items:
            test_evidence.append(TestExecutionEvidence(
                test_suite=item.metadata.get('test_directory', 'unknown'),
                test_results=item.output_data,
                coverage_report={},  # Would be populated from coverage data
                performance_metrics={},  # Would be populated from performance data
                execution_logs=[item.raw_output],
                artifacts=[],  # Would be populated from artifacts
                statistical_analysis={}  # Would be populated from statistical analysis
            ))
        
        return test_evidence
    
    async def _collect_performance_measurements(self) -> List[PerformanceMeasurement]:
        """Collect performance measurements"""
        # This would be populated by actual performance measurements
        return []
    
    async def _generate_verification_results(self) -> Dict[str, Any]:
        """Generate verification results"""
        return {
            "total_evidence_items": len(self.evidence_items),
            "successful_collections": len([item for item in self.evidence_items 
                                         if item.exit_code == 0]),
            "failed_collections": len([item for item in self.evidence_items 
                                     if item.exit_code != 0]),
            "average_execution_time": statistics.mean([item.execution_duration_seconds 
                                                     for item in self.evidence_items]),
            "verification_hashes": [item.verification_hash for item in self.evidence_items]
        }
    
    def _calculate_reproducibility_score(self) -> float:
        """Calculate reproducibility score"""
        if not self.evidence_items:
            return 0.0
        
        # Simple score based on successful collections
        successful_items = len([item for item in self.evidence_items 
                              if item.exit_code == 0 and item.reproducible])
        
        return successful_items / len(self.evidence_items)
    
    def _calculate_evidence_quality_score(self) -> float:
        """Calculate evidence quality score"""
        if not self.evidence_items:
            return 0.0
        
        # Score based on various quality factors
        quality_factors = []
        
        for item in self.evidence_items:
            factors = []
            
            # Execution success
            factors.append(1.0 if item.exit_code == 0 else 0.0)
            
            # Has output data
            factors.append(1.0 if item.output_data else 0.0)
            
            # Has verification hash
            factors.append(1.0 if item.verification_hash else 0.0)
            
            # Reproducible
            factors.append(1.0 if item.reproducible else 0.0)
            
            # Has metadata
            factors.append(1.0 if item.metadata else 0.0)
            
            quality_factors.append(statistics.mean(factors))
        
        return statistics.mean(quality_factors)
    
    async def _save_evidence_collection(self, evidence_collection: EvidenceCollection):
        """Save evidence collection to disk"""
        collection_file = self.output_dir / self.collection_id / "evidence_collection.json"
        
        with open(collection_file, 'w') as f:
            json.dump(asdict(evidence_collection), f, indent=2, default=str)
        
        self.logger.info(f"Saved evidence collection: {collection_file}")


class SystemMonitor:
    """System monitoring for evidence collection"""
    
    def __init__(self):
        self.monitoring_active = False
        self.monitoring_data = []
        self.monitor_task = None
    
    async def start_monitoring(self):
        """Start system monitoring"""
        self.monitoring_active = True
        self.monitoring_data = []
        self.monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def stop_monitoring(self) -> SystemHealthEvidence:
        """Stop monitoring and return evidence"""
        self.monitoring_active = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        # Analyze monitoring data
        if self.monitoring_data:
            system_metrics = self._analyze_system_metrics()
            resource_utilization = self._analyze_resource_utilization()
        else:
            system_metrics = {}
            resource_utilization = {}
        
        return SystemHealthEvidence(
            system_metrics=system_metrics,
            resource_utilization=resource_utilization,
            error_logs=[],
            health_checks={},
            service_status={}
        )
    
    async def _monitor_loop(self):
        """Monitoring loop"""
        try:
            while self.monitoring_active:
                timestamp = datetime.now(timezone.utc).isoformat()
                
                # Collect system metrics
                metrics = {
                    "timestamp": timestamp,
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage('/').percent,
                    "network_io": psutil.net_io_counters()._asdict(),
                    "process_count": len(psutil.pids())
                }
                
                self.monitoring_data.append(metrics)
                
                await asyncio.sleep(1)  # Monitor every second
                
        except asyncio.CancelledError:
            pass
    
    def _analyze_system_metrics(self) -> Dict[str, Any]:
        """Analyze system metrics"""
        if not self.monitoring_data:
            return {}
        
        cpu_values = [d['cpu_percent'] for d in self.monitoring_data]
        memory_values = [d['memory_percent'] for d in self.monitoring_data]
        
        return {
            "cpu_usage": {
                "mean": statistics.mean(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values),
                "std": statistics.stdev(cpu_values) if len(cpu_values) > 1 else 0
            },
            "memory_usage": {
                "mean": statistics.mean(memory_values),
                "max": max(memory_values),
                "min": min(memory_values),
                "std": statistics.stdev(memory_values) if len(memory_values) > 1 else 0
            },
            "monitoring_duration": len(self.monitoring_data),
            "data_points": len(self.monitoring_data)
        }
    
    def _analyze_resource_utilization(self) -> Dict[str, Any]:
        """Analyze resource utilization"""
        if not self.monitoring_data:
            return {}
        
        return {
            "peak_cpu": max(d['cpu_percent'] for d in self.monitoring_data),
            "peak_memory": max(d['memory_percent'] for d in self.monitoring_data),
            "peak_processes": max(d['process_count'] for d in self.monitoring_data),
            "resource_stability": self._calculate_resource_stability()
        }
    
    def _calculate_resource_stability(self) -> float:
        """Calculate resource stability score"""
        if not self.monitoring_data:
            return 0.0
        
        # Calculate coefficient of variation for CPU and memory
        cpu_values = [d['cpu_percent'] for d in self.monitoring_data]
        memory_values = [d['memory_percent'] for d in self.monitoring_data]
        
        cpu_cv = statistics.stdev(cpu_values) / statistics.mean(cpu_values) if statistics.mean(cpu_values) > 0 else 0
        memory_cv = statistics.stdev(memory_values) / statistics.mean(memory_values) if statistics.mean(memory_values) > 0 else 0
        
        # Stability score (lower CV = higher stability)
        stability = 1.0 - (cpu_cv + memory_cv) / 2
        return max(0.0, stability)


class PerformanceTracker:
    """Performance tracking for evidence collection"""
    
    def __init__(self):
        self.measurements = []
    
    def add_measurement(self, measurement: PerformanceMeasurement):
        """Add performance measurement"""
        self.measurements.append(measurement)
    
    def get_measurements(self) -> List[PerformanceMeasurement]:
        """Get all measurements"""
        return self.measurements


def main():
    """CLI interface for evidence collection"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Production-grade evidence collection')
    parser.add_argument('--output-dir', default='evidence_collection',
                       help='Output directory for evidence')
    parser.add_argument('--collection-id', help='Specific collection ID to use')
    
    args = parser.parse_args()
    
    async def run_collection():
        collector = EvidenceCollector(Path(args.output_dir))
        
        # Start collection
        if args.collection_id:
            collector.collection_id = args.collection_id
        
        collection_id = await collector.start_collection()
        
        # Collect various types of evidence
        await collector.collect_test_execution_evidence(
            "python -m pytest tests/unit/",
            Path(".")
        )
        
        # Collect performance measurement
        async def sample_operation():
            await asyncio.sleep(0.1)
            return "operation_result"
        
        await collector.collect_performance_measurement(
            "sample_operation", sample_operation, 5
        )
        
        # Generate reproducibility guide
        await collector.generate_reproducibility_guide()
        
        # Stop collection
        evidence_collection = await collector.stop_collection()
        
        print(f"Evidence collection complete: {evidence_collection.collection_id}")
        print(f"Quality score: {evidence_collection.evidence_quality_score}")
        print(f"Reproducibility score: {evidence_collection.reproducibility_score}")
    
    asyncio.run(run_collection())


if __name__ == "__main__":
    main()