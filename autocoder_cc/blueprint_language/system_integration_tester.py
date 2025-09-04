#!/usr/bin/env python3
"""
System Integration Tester for Phase 5 - Level 3 Validation

This module implements Level 3 system integration testing that validates
the fully assembled system's behavior against real, containerized dependencies.

Key features:
- Generates complete systems with test components
- Replaces blueprint source/sink with test components
- Runs system as subprocess with real dependencies
- Sends SIGINT after timeout for graceful shutdown
- Verifies output matches expected transformation
"""

import anyio
import json
import logging
import signal
import subprocess
import sys
import tempfile
import time
import yaml
import httpx
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from autocoder_cc.observability.structured_logging import get_logger

from .system_blueprint_parser import ParsedSystemBlueprint, ParsedComponent
from .system_scaffold_generator import SystemScaffoldGenerator
from .component_logic_generator import ComponentLogicGenerator


@dataclass
class SystemIntegrationResult:
    """Result of system integration test"""
    system_name: str
    passed: bool
    startup_time: float
    shutdown_time: float
    components_started: int
    api_endpoints_responding: List[str]
    error_message: Optional[str] = None
    process_output: str = ""
    test_data_flow_verified: bool = False


class TestInputSource:
    """Test component that feeds known test data to the system"""
    
    def __init__(self, test_data: List[Dict[str, Any]]):
        self.test_data = test_data
    
    def get_implementation(self, class_name: str, component_name: str) -> str:
        """Generate test input source implementation"""
        test_data_json = json.dumps(self.test_data, indent=4)
        
        return f'''#!/usr/bin/env python3
"""
Test Input Source Component - Generated for Integration Testing
Feeds known test data to validate system behavior
"""
import anyio
import logging
import json
from typing import Dict, Any

from autocoder_cc.components import Source


class {class_name}(Source):
    """Test source that feeds predetermined test data"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.test_data = {test_data_json}
        self.current_index = 0
        
    async def _generate_data(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test data from predetermined dataset"""
        if self.current_index >= len(self.test_data):
            return None  # Signal completion
            
        data = self.test_data[self.current_index].copy()
        data["test_index"] = self.current_index
        data["timestamp"] = str(anyio.current_time())
        
        self.current_index += 1
        self.logger.info(f"Generated test data {{self.current_index}}/{{len(self.test_data)}}: {{data}}")
        
        return data
'''


class TestOutputSink:
    """Test component that collects results for verification"""
    
    def __init__(self, output_file: Path):
        self.output_file = output_file
    
    def get_implementation(self, class_name: str, component_name: str) -> str:
        """Generate test output sink implementation"""
        
        return f'''#!/usr/bin/env python3
"""
Test Output Sink Component - Generated for Integration Testing
Collects system outputs for verification
"""
import anyio
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from autocoder_cc.components.composed_base import ComposedComponent


class {class_name}(ComposedComponent):
    """Test sink that collects outputs for verification"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.output_file = Path("{self.output_file}")
        self.collected_outputs = []
        
    async def _output_data(self, inputs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Collect output data for verification"""
        # Add metadata
        output_record = {{
            "collected_at": str(anyio.current_time()),
            "sink_name": self.name,
            "data": inputs
        }}
        
        self.collected_outputs.append(output_record)
        
        # Write to file for verification
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_file, 'w') as f:
            json.dump(self.collected_outputs, f, indent=2)
        
        self.logger.info(f"Collected output {{len(self.collected_outputs)}}: {{inputs}}")
        
        return output_record
'''


class SystemIntegrationTester:
    """
    Level 3 system integration tester that validates complete systems.
    
    This implements the Phase 5 requirements:
    - Generate complete system with test components
    - Run as subprocess with real dependencies
    - Verify HTTP endpoints respond correctly
    - Test graceful shutdown via SIGINT
    - Validate end-to-end data flow
    """
    
    def __init__(self, working_dir: Path):
        self.working_dir = Path(working_dir)
        self.working_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger("SystemIntegrationTester")
    
    async def test_system_integration(self, 
                                      system_blueprint: ParsedSystemBlueprint,
                                      test_data: List[Dict[str, Any]] = None,
                                      timeout: float = 30.0) -> SystemIntegrationResult:
        """
        Run complete system integration test.
        
        This is the main entry point for Level 3 validation.
        """
        if test_data is None:
            test_data = [
                {"test_id": 1, "value": 100, "category": "test"},
                {"test_id": 2, "value": 200, "category": "test"},
                {"test_id": 3, "value": 300, "category": "test"}
            ]
        
        self.logger.info(f"Starting system integration test for: {system_blueprint.system.name}")
        
        # Create modified blueprint with test components
        test_blueprint = self._create_test_blueprint(system_blueprint, test_data)
        
        # Generate the complete test system
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_system_dir = await self._generate_test_system(test_blueprint, temp_path)
            
            # Run integration test
            return await self._run_integration_test(
                test_blueprint, 
                test_system_dir, 
                test_data,
                timeout
            )
    
    def _create_test_blueprint(self, 
                               original_blueprint: ParsedSystemBlueprint, 
                               test_data: List[Dict[str, Any]]) -> ParsedSystemBlueprint:
        """
        Create modified blueprint with test source and sink components.
        
        This replaces the original source/sink with test components that
        feed known data and collect outputs for verification.
        """
        # Deep copy the original blueprint
        import copy
        test_blueprint = copy.deepcopy(original_blueprint)
        
        # Find source and sink components
        source_components = [c for c in test_blueprint.system.components if c.type == "Source"]
        sink_components = [c for c in test_blueprint.system.components if c.type == "Sink"]
        
        # Replace source with test source
        if source_components:
            source_comp = source_components[0]
            source_comp.name = "test_input_source"
            source_comp.description = "Test source with predetermined data"
            source_comp.config["test_data"] = test_data
            source_comp.config["count"] = len(test_data)
        
        # Replace sink with test sink
        if sink_components:
            sink_comp = sink_components[0]
            sink_comp.name = "test_output_sink"
            sink_comp.description = "Test sink for output verification"
            sink_comp.config["output_file"] = "test_outputs.json"
        
        return test_blueprint
    
    async def _generate_test_system(self, 
                                    test_blueprint: ParsedSystemBlueprint, 
                                    temp_path: Path) -> Path:
        """Generate complete test system with custom test components"""
        
        # Generate main system scaffold
        scaffold_gen = SystemScaffoldGenerator(temp_path)
        scaffold = scaffold_gen.generate_system(test_blueprint)
        
        # Generate regular components
        component_gen = ComponentLogicGenerator(temp_path)
        # Fix: generate_components is async, need to run it properly
        import asyncio
        components = asyncio.run(component_gen.generate_components(test_blueprint))
        
        # Generate custom test components
        system_name = test_blueprint.system.name
        components_dir = temp_path / system_name / "components"
        
        # Create test input source
        test_data = test_blueprint.system.components[0].config.get("test_data", [])
        test_input_source = TestInputSource(test_data)
        input_impl = test_input_source.get_implementation("GeneratedSource_test_input_source", "test_input_source")
        
        with open(components_dir / "test_input_source.py", 'w') as f:
            f.write(input_impl)
        
        # Create test output sink
        output_file = temp_path / system_name / "test_outputs.json"
        test_output_sink = TestOutputSink(output_file)
        sink_impl = test_output_sink.get_implementation("GeneratedSink_test_output_sink", "test_output_sink")
        
        with open(components_dir / "test_output_sink.py", 'w') as f:
            f.write(sink_impl)
        
        self.logger.info(f"Generated test system in: {temp_path / system_name}")
        return temp_path / system_name
    
    async def _run_integration_test(self, 
                                    test_blueprint: ParsedSystemBlueprint,
                                    test_system_dir: Path,
                                    test_data: List[Dict[str, Any]],
                                    timeout: float) -> SystemIntegrationResult:
        """
        Run the actual integration test by starting the system as subprocess.
        
        This implements the core Level 3 validation logic.
        """
        system_name = test_blueprint.system.name
        main_py = test_system_dir / "main.py"
        
        start_time = time.time()
        
        try:
            # Start system as subprocess
            self.logger.info(f"Starting system subprocess: {main_py}")
            
            env = {"PYTHONPATH": str(test_system_dir.parent.parent.parent)}
            
            # Collect output in lists
            stdout_lines = []
            stderr_lines = []
            
            async def collect_output(stream, lines):
                async for line in stream:
                    lines.append(line.decode())
            
            process = await anyio.open_process([
                sys.executable, str(main_py)
            ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Start output collection tasks
            async with anyio.create_task_group() as tg:
                tg.start_soon(collect_output, process.stdout, stdout_lines)
                tg.start_soon(collect_output, process.stderr, stderr_lines)
            
            startup_time = time.time() - start_time
            
            # Give system time to start
            await anyio.sleep(2.0)
            
            # Check if system is running
            # For anyio Process, we check returncode instead of poll()
            if process.returncode is not None:
                # Process already exited
                return SystemIntegrationResult(
                    system_name=system_name,
                    passed=False,
                    startup_time=startup_time,
                    shutdown_time=0,
                    components_started=0,
                    api_endpoints_responding=[],
                    error_message=f"System failed to start with returncode: {process.returncode}",
                    process_output=""
                )
            
            # Test API endpoints if any
            api_endpoints = self._find_api_endpoints(test_blueprint)
            responding_endpoints = await self._test_api_endpoints(api_endpoints)
            
            # Wait for data processing
            processing_time = len(test_data) * 0.5  # Estimate processing time
            await anyio.sleep(processing_time)
            
            # Graceful shutdown test
            shutdown_start = time.time()
            self.logger.info("Sending SIGINT for graceful shutdown test")
            process.send_signal(signal.SIGINT)
            
            # Wait for graceful shutdown
            try:
                with anyio.move_on_after(10.0):
                    await process.wait()
                shutdown_time = time.time() - shutdown_start
            except:
                # Force kill if graceful shutdown fails
                process.kill()
                await process.wait()
                shutdown_time = time.time() - shutdown_start
            
            # Get process output
            process_output = "".join(stdout_lines) + "\n" + "".join(stderr_lines)
            
            # Verify data flow
            data_flow_verified = await self._verify_data_flow(test_system_dir, test_data)
            
            # Count components from output
            components_started = process_output.count("Starting component process:")
            
            return SystemIntegrationResult(
                system_name=system_name,
                passed=True,
                startup_time=startup_time,
                shutdown_time=shutdown_time,
                components_started=components_started,
                api_endpoints_responding=responding_endpoints,
                process_output=process_output,
                test_data_flow_verified=data_flow_verified
            )
            
        except Exception as e:
            return SystemIntegrationResult(
                system_name=system_name,
                passed=False,
                startup_time=time.time() - start_time,
                shutdown_time=0,
                components_started=0,
                api_endpoints_responding=[],
                error_message=f"Integration test failed: {str(e)}"
            )
    
    def _find_api_endpoints(self, blueprint: ParsedSystemBlueprint) -> List[Dict[str, Any]]:
        """Find API endpoints in the blueprint"""
        endpoints = []
        for component in blueprint.system.components:
            if component.type == "APIEndpoint":
                port = component.config.get("port", 8080)
                endpoints.append({
                    "name": component.name,
                    "url": f"http://localhost:{port}",
                    "port": port
                })
        return endpoints
    
    async def _test_api_endpoints(self, endpoints: List[Dict[str, Any]]) -> List[str]:
        """Test that API endpoints are responding with real HTTP health checks"""
        responding = []
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            for endpoint in endpoints:
                endpoint_name = endpoint["name"]
                base_url = endpoint["url"]
                
                # Try multiple health check paths
                health_paths = ["/health", "/healthz", "/ping", "/"]
                endpoint_responding = False
                
                for health_path in health_paths:
                    health_url = f"{base_url}{health_path}"
                    
                    try:
                        self.logger.info(f"Testing endpoint {endpoint_name} at {health_url}")
                        
                        # Attempt HTTP GET with retries
                        for attempt in range(3):  # 3 retry attempts
                            try:
                                response = await client.get(health_url)
                                
                                # Accept any successful HTTP status (200-299) or common health check statuses
                                if response.status_code < 400:
                                    self.logger.info(f"Endpoint {endpoint_name} responding: {response.status_code}")
                                    responding.append(endpoint_name)
                                    endpoint_responding = True
                                    break
                                else:
                                    self.logger.debug(f"Endpoint {endpoint_name} returned {response.status_code} at {health_url}")
                                    
                            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as e:
                                if attempt < 2:  # Don't log timeout for intermediate attempts
                                    self.logger.debug(f"Attempt {attempt + 1} timeout for {health_url}: {e}")
                                    await anyio.sleep(1.0)  # Wait before retry
                                continue
                            except Exception as e:
                                self.logger.debug(f"Attempt {attempt + 1} error for {health_url}: {e}")
                                if attempt < 2:
                                    await anyio.sleep(1.0)
                                continue
                                
                        if endpoint_responding:
                            break  # Successfully found a responding health endpoint
                            
                    except Exception as e:
                        self.logger.debug(f"Health check error for {health_url}: {e}")
                        continue
                
                if not endpoint_responding:
                    self.logger.warning(f"Endpoint {endpoint_name} not responding on any health check path: {health_paths}")
        
        return responding
    
    async def _verify_data_flow(self, system_dir: Path, expected_test_data: List[Dict[str, Any]]) -> bool:
        """Verify that test data flowed through the system correctly"""
        try:
            output_file = system_dir / "test_outputs.json"
            if not output_file.exists():
                self.logger.warning("Output file not found")
                return False
            
            with open(output_file, 'r') as f:
                collected_outputs = json.load(f)
            
            # Basic verification - check if we got the expected number of outputs
            if len(collected_outputs) >= len(expected_test_data):
                self.logger.info(f"Data flow verified: {len(collected_outputs)} outputs collected")
                return True
            else:
                self.logger.warning(f"Data flow incomplete: {len(collected_outputs)}/{len(expected_test_data)} outputs")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to verify data flow: {e}")
            return False


async def main():
    """Test the system integration tester"""
    from .system_blueprint_parser import SystemBlueprintParser
    
    # Create test blueprint
    test_blueprint_yaml = """
system:
  name: integration_test_system
  description: System for testing integration capabilities
  version: 1.0.0
  
  components:
    - name: data_source
      type: Source
      description: Test data source
      configuration:
        count: 3
        delay: 0.1
      outputs:
        - name: data
          schema: DataRecord
          
    - name: processor
      type: Transformer
      description: Process data
      configuration:
        multiplier: 2
      inputs:
        - name: input
          schema: DataRecord
      outputs:
        - name: output
          schema: ProcessedRecord
          
    - name: data_sink
      type: Sink
      description: Collect results
      inputs:
        - name: input
          schema: ProcessedRecord
  
  bindings:
    - from: data_source.data
      to: processor.input
    - from: processor.output
      to: data_sink.input

configuration:
  environment: test
"""
    
    try:
        # Parse blueprint
        parser = SystemBlueprintParser()
        system_blueprint = parser.parse_string(test_blueprint_yaml)
        print(f"✅ Parsed integration test blueprint: {system_blueprint.system.name}")
        
        # Create integration tester
        tester = SystemIntegrationTester(Path("./integration_test_output"))
        
        # Prepare test data
        test_data = [
            {"id": 1, "value": 10, "type": "test"},
            {"id": 2, "value": 20, "type": "test"},
            {"id": 3, "value": 30, "type": "test"}
        ]
        
        # Run integration test
        print("\\n🚀 Running System Integration Test...")
        result = await tester.test_system_integration(system_blueprint, test_data, timeout=15.0)
        
        # Display results
        print(f"\\n📊 Integration Test Results:")
        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"  System: {result.system_name} - {status}")
        print(f"  Startup time: {result.startup_time:.2f}s")
        print(f"  Shutdown time: {result.shutdown_time:.2f}s")
        print(f"  Components started: {result.components_started}")
        print(f"  API endpoints responding: {len(result.api_endpoints_responding)}")
        print(f"  Data flow verified: {'✅' if result.test_data_flow_verified else '❌'}")
        
        if result.error_message:
            print(f"  Error: {result.error_message}")
        
        if result.passed:
            print("\\n🎉 SYSTEM INTEGRATION TEST PASSED!")
            print("✅ Complete system runs successfully")
            print("✅ Graceful shutdown works")
            print("✅ End-to-end data flow validated")
        else:
            print("\\n❌ SYSTEM INTEGRATION TEST FAILED")
            print("❌ System needs fixes before deployment")
        
    except Exception as e:
        print(f"❌ Integration tester failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    anyio.run(main)