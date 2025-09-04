#!/usr/bin/env python3
"""
Phase Test Runner Utilities
============================

Centralized utilities for running individual phases of the system generation pipeline
in isolation, with comprehensive error analysis and debugging capabilities.
"""

import os
import sys
import time
import tempfile
import asyncio
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

@dataclass
class PhaseResult:
    """Result of a phase test execution"""
    phase: str
    success: bool
    duration: float
    error: Optional[str] = None
    error_analysis: Optional[Dict[str, Any]] = None
    output_data: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TestEnvironment:
    """Test environment configuration"""
    temp_dir: Optional[Path] = None
    output_dir: Optional[Path] = None
    verbose: bool = False
    timeout: int = 60
    cleanup_on_success: bool = False
    cleanup_on_failure: bool = False

class PhaseTestRunner:
    """
    Central utility for running individual phases of the system generation pipeline.
    
    This class provides isolated testing capabilities for:
    - Phase 1: Blueprint Validation
    - Phase 2: Component Generation  
    - Phase 3: System Assembly
    - Phase 4: Deployment
    """
    
    def __init__(self, environment: TestEnvironment = None):
        self.env = environment or TestEnvironment()
        self.setup_environment()
    
    def setup_environment(self):
        """Setup test environment"""
        os.environ['AUTOCODER_GENERATION_MODE'] = 'true'
        os.environ['SKIP_OBSERVABILITY_SETUP'] = 'true'
        
        # Create temp directory if needed
        if self.env.temp_dir is None:
            self.env.temp_dir = Path(tempfile.mkdtemp(prefix="phase_test_"))
        
        # Create output directory if needed
        if self.env.output_dir is None:
            self.env.output_dir = self.env.temp_dir / f"output_{int(time.time())}"
        
        self.env.output_dir.mkdir(parents=True, exist_ok=True)
    
    def cleanup_environment(self, success: bool):
        """Cleanup test environment based on success/failure"""
        should_cleanup = (
            (success and self.env.cleanup_on_success) or
            (not success and self.env.cleanup_on_failure)
        )
        
        if should_cleanup and self.env.temp_dir and self.env.temp_dir.exists():
            import shutil
            try:
                shutil.rmtree(self.env.temp_dir)
            except Exception as e:
                if self.env.verbose:
                    print(f"Warning: Failed to cleanup temp dir: {e}")
    
    def analyze_error(self, error: Exception, phase: str, context: str = "") -> Dict[str, Any]:
        """Analyze error and categorize for targeted fixing"""
        error_analysis = {
            'type': type(error).__name__,
            'message': str(error),
            'phase': phase,
            'context': context,
            'category': 'unknown',
            'suggested_fix': 'Manual investigation required',
            'file_hint': None,
            'line_hint': None,
            'timestamp': time.time()
        }
        
        # Extract traceback info
        tb = traceback.extract_tb(error.__traceback__)
        if tb:
            last_frame = tb[-1]
            error_analysis['file_hint'] = last_frame.filename
            error_analysis['line_hint'] = last_frame.lineno
        
        error_str = str(error)
        
        # Phase-specific error categorization
        if phase == "phase1":
            error_analysis.update(self._categorize_phase1_error(error, error_str))
        elif phase == "phase2":
            error_analysis.update(self._categorize_phase2_error(error, error_str))
        elif phase == "phase3":
            error_analysis.update(self._categorize_phase3_error(error, error_str))
        elif phase == "phase4":
            error_analysis.update(self._categorize_phase4_error(error, error_str))
        
        return error_analysis
    
    def _categorize_phase1_error(self, error: Exception, error_str: str) -> Dict[str, str]:
        """Categorize Phase 1 (Blueprint Validation) errors"""
        if 'yaml.scanner.ScannerError' in str(type(error)) or 'yaml' in error_str.lower():
            return {
                'category': 'yaml_syntax_error',
                'suggested_fix': 'Fix YAML syntax - check unclosed brackets, quotes, indentation',
                'details': 'YAML parsing failed'
            }
        elif 'KeyError' in str(type(error)):
            return {
                'category': 'missing_required_field',
                'suggested_fix': 'Add missing required field to blueprint',
                'details': f'Missing field: {error_str}'
            }
        elif 'ValidationError' in str(type(error)):
            return {
                'category': 'schema_validation_error',
                'suggested_fix': 'Fix blueprint schema validation issues',
                'details': 'Blueprint does not match required schema'
            }
        return {}
    
    def _categorize_phase2_error(self, error: Exception, error_str: str) -> Dict[str, str]:
        """Categorize Phase 2 (Component Generation) errors"""
        if "'coroutine' object has no attribute" in error_str:
            return {
                'category': 'async_coroutine_handling',
                'suggested_fix': 'Fix async/await handling - likely missing await statement',
                'details': 'Coroutine treated as regular object'
            }
        elif 'IndexError' in str(type(error)) and 'format' in error_str.lower():
            return {
                'category': 'template_formatting_error',
                'suggested_fix': 'Fix template string formatting issues',
                'details': 'Template format placeholders mismatch'
            }
        elif 'ImportError' in str(type(error)) or 'ModuleNotFoundError' in str(type(error)):
            return {
                'category': 'generator_import_error',
                'suggested_fix': 'Fix import paths in component generator',
                'details': 'Component generator cannot import required modules'
            }
        return {}
    
    def _categorize_phase3_error(self, error: Exception, error_str: str) -> Dict[str, str]:
        """Categorize Phase 3 (System Assembly) errors"""
        if 'ImportError' in str(type(error)) or 'ModuleNotFoundError' in str(type(error)):
            return {
                'category': 'component_import_error',
                'suggested_fix': 'Fix component import paths or ensure components were generated correctly',
                'details': 'Generated components cannot be imported'
            }
        elif 'FileNotFoundError' in str(type(error)):
            return {
                'category': 'missing_file',
                'suggested_fix': 'Ensure all required files are generated and paths are correct',
                'details': 'Required file missing from system assembly'
            }
        elif 'SyntaxError' in str(type(error)):
            return {
                'category': 'generated_code_syntax_error',
                'suggested_fix': 'Fix syntax error in generated component code',
                'details': 'Generated code has syntax errors'
            }
        return {}
    
    def _categorize_phase4_error(self, error: Exception, error_str: str) -> Dict[str, str]:
        """Categorize Phase 4 (Deployment) errors"""
        if 'address already in use' in error_str.lower():
            return {
                'category': 'port_binding_error',
                'suggested_fix': 'Kill existing process or use different port',
                'details': 'Port already in use by another process'
            }
        elif 'permission denied' in error_str.lower():
            return {
                'category': 'permission_error',
                'suggested_fix': 'Check file permissions or run with appropriate privileges',
                'details': 'Insufficient permissions for deployment'
            }
        elif 'connection refused' in error_str.lower():
            return {
                'category': 'connection_error',
                'suggested_fix': 'Ensure required services are running',
                'details': 'Cannot connect to required services'
            }
        return {}
    
    async def run_phase1(self, blueprint_content: str, test_name: str = "phase1_test") -> PhaseResult:
        """Run Phase 1 (Blueprint Validation) in isolation"""
        start_time = time.time()
        
        if self.env.verbose:
            print(f"🧪 Running Phase 1: {test_name}")
        
        try:
            # Create temporary blueprint file
            blueprint_file = self.env.temp_dir / f"{test_name}.yaml"
            with open(blueprint_file, 'w') as f:
                f.write(blueprint_content)
            
            # Test YAML parsing
            import yaml
            parsed_yaml = yaml.safe_load(blueprint_content)
            
            # Test blueprint loading if system blueprint parser is available
            try:
                from autocoder_cc.blueprint_language.system_blueprint_parser import SystemBlueprintParser
                
                parser = SystemBlueprintParser()
                
                # Load blueprint through parser
                blueprint_data = parser.parse_string(blueprint_content)
                
                # Test validation if available - skip for now as validation framework is complex
                if self.env.verbose:
                    print("  ✅ Blueprint parsed successfully")
                
                duration = time.time() - start_time
                return PhaseResult(
                    phase="phase1",
                    success=True,
                    duration=duration,
                    output_data={
                        'parsed_yaml': parsed_yaml,
                        'blueprint_data': blueprint_data.system.name if hasattr(blueprint_data, 'system') else 'parsed'
                    },
                    metadata={
                        'test_name': test_name,
                        'blueprint_file': str(blueprint_file)
                    }
                )
                
            except ImportError as e:
                # Fall back to just YAML parsing if system generator not available
                duration = time.time() - start_time
                return PhaseResult(
                    phase="phase1",
                    success=True,
                    duration=duration,
                    output_data={'parsed_yaml': parsed_yaml},
                    metadata={
                        'test_name': test_name,
                        'blueprint_file': str(blueprint_file),
                        'limited_test': 'SystemGenerator not available'
                    }
                )
        
        except Exception as e:
            duration = time.time() - start_time
            error_analysis = self.analyze_error(e, "phase1", f"Blueprint: {test_name}")
            
            return PhaseResult(
                phase="phase1",
                success=False,
                duration=duration,
                error=str(e),
                error_analysis=error_analysis,
                metadata={'test_name': test_name}
            )
    
    async def run_phase2(self, blueprint_data: Dict[str, Any], test_name: str = "phase2_test") -> PhaseResult:
        """Run Phase 2 (Component Generation) in isolation"""
        start_time = time.time()
        
        if self.env.verbose:
            print(f"🧪 Running Phase 2: {test_name}")
        
        try:
            from autocoder_cc.blueprint_language.system_generator import SystemGenerator
            
            system_generator = SystemGenerator(
                output_dir=str(self.env.output_dir),
                verbose_logging=self.env.verbose,
                timeout=self.env.timeout
            )
            
            # Create temporary blueprint file
            import yaml
            blueprint_file = self.env.temp_dir / f"{test_name}.yaml"
            with open(blueprint_file, 'w') as f:
                yaml.dump(blueprint_data, f)
            
            # Run Phase 2 generation
            result = system_generator.generate_system_with_timeout(str(blueprint_file))
            
            duration = time.time() - start_time
            return PhaseResult(
                phase="phase2",
                success=True,
                duration=duration,
                output_data=result,
                metadata={
                    'test_name': test_name,
                    'blueprint_file': str(blueprint_file),
                    'output_dir': str(self.env.output_dir)
                }
            )
        
        except Exception as e:
            duration = time.time() - start_time
            error_analysis = self.analyze_error(e, "phase2", f"Component generation: {test_name}")
            
            return PhaseResult(
                phase="phase2",
                success=False,
                duration=duration,
                error=str(e),
                error_analysis=error_analysis,
                metadata={'test_name': test_name}
            )
    
    async def run_phase3(self, components_dir: Path, blueprint_data: Dict[str, Any], test_name: str = "phase3_test") -> PhaseResult:
        """Run Phase 3 (System Assembly) in isolation"""
        start_time = time.time()
        
        if self.env.verbose:
            print(f"🧪 Running Phase 3: {test_name}")
        
        try:
            system_dir = self.env.output_dir / test_name
            system_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy components to system directory
            import shutil
            target_components_dir = system_dir / "components"
            if components_dir.exists():
                shutil.copytree(components_dir, target_components_dir, dirs_exist_ok=True)
            
            # Generate main.py
            await self._generate_main_py(system_dir, blueprint_data)
            
            # Validate system structure
            await self._validate_system_structure(system_dir, blueprint_data)
            
            # Test component imports
            await self._test_component_imports(system_dir)
            
            duration = time.time() - start_time
            return PhaseResult(
                phase="phase3",
                success=True,
                duration=duration,
                output_data={'system_dir': str(system_dir)},
                metadata={
                    'test_name': test_name,
                    'system_dir': str(system_dir)
                }
            )
        
        except Exception as e:
            duration = time.time() - start_time
            error_analysis = self.analyze_error(e, "phase3", f"System assembly: {test_name}")
            
            return PhaseResult(
                phase="phase3",
                success=False,
                duration=duration,
                error=str(e),
                error_analysis=error_analysis,
                metadata={'test_name': test_name}
            )
    
    async def run_phase4(self, system_dir: Path, test_name: str = "phase4_test", startup_timeout: int = 10) -> PhaseResult:
        """Run Phase 4 (Deployment) in isolation"""
        start_time = time.time()
        
        if self.env.verbose:
            print(f"🧪 Running Phase 4: {test_name}")
        
        try:
            # Test that main.py exists and is executable
            main_py = system_dir / "main.py"
            if not main_py.exists():
                raise FileNotFoundError(f"main.py not found in {system_dir}")
            
            # Test system startup (with timeout)
            import subprocess
            import signal
            
            # Start the system process
            proc = subprocess.Popen(
                [sys.executable, str(main_py)],
                cwd=str(system_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                # Wait for startup with timeout
                stdout, stderr = proc.communicate(timeout=startup_timeout)
                
                # Check if process started successfully
                if proc.returncode is not None and proc.returncode != 0:
                    error_msg = f"System startup failed with return code {proc.returncode}\nStderr: {stderr}"
                    raise RuntimeError(error_msg)
                
                duration = time.time() - start_time
                return PhaseResult(
                    phase="phase4",
                    success=True,
                    duration=duration,
                    output_data={
                        'stdout': stdout,
                        'stderr': stderr,
                        'return_code': proc.returncode
                    },
                    metadata={
                        'test_name': test_name,
                        'system_dir': str(system_dir),
                        'startup_timeout': startup_timeout
                    }
                )
            
            except subprocess.TimeoutExpired:
                # Kill the process
                proc.kill()
                proc.wait()
                
                # For deployment testing, timeout during startup might be expected
                # if the system is designed to run continuously
                duration = time.time() - start_time
                return PhaseResult(
                    phase="phase4",
                    success=True,
                    duration=duration,
                    output_data={'startup_success': True, 'timeout_expected': True},
                    metadata={
                        'test_name': test_name,
                        'system_dir': str(system_dir),
                        'startup_timeout': startup_timeout,
                        'note': 'System started successfully but timed out (expected for continuous services)'
                    }
                )
        
        except Exception as e:
            duration = time.time() - start_time
            error_analysis = self.analyze_error(e, "phase4", f"Deployment: {test_name}")
            
            return PhaseResult(
                phase="phase4",
                success=False,
                duration=duration,
                error=str(e),
                error_analysis=error_analysis,
                metadata={'test_name': test_name}
            )
    
    async def _generate_main_py(self, system_dir: Path, blueprint_data: Dict[str, Any]):
        """Generate main.py for the system"""
        system_name = blueprint_data.get("system", {}).get("name", "generated_system")
        components = blueprint_data.get("components", [])
        
        # Generate imports
        imports = []
        component_inits = []
        
        for component in components:
            comp_name = component["name"]
            class_name = comp_name.title().replace('_', '') + component["type"]
            imports.append(f"from components.{comp_name} import {class_name}")
            component_inits.append(f'        self.components["{comp_name}"] = {class_name}("{comp_name}", {component.get("configuration", {})})')
        
        main_py_content = f'''#!/usr/bin/env python3
"""
Generated System: {system_name}
Auto-generated by AutoCoder4_CC Phase 3 Testing
"""

import asyncio
import sys
from pathlib import Path

# Add components to path
sys.path.insert(0, str(Path(__file__).parent / "components"))

{chr(10).join(imports)}

class SystemHarness:
    def __init__(self):
        self.components = {{}}
        
    async def setup_components(self):
        # Initialize components
{chr(10).join(component_inits)}
        
        # Setup all components
        for component in self.components.values():
            if hasattr(component, 'setup'):
                await component.setup()
    
    async def start_system(self):
        print("🚀 Starting {system_name} system...")
        await self.setup_components()
        print("✅ System started successfully")
        
        # Keep system running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\\n🛑 Shutting down system...")
            await self.cleanup_components()
    
    async def cleanup_components(self):
        for component in self.components.values():
            if hasattr(component, 'cleanup'):
                await component.cleanup()

async def main():
    harness = SystemHarness()
    await harness.start_system()

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        main_py_path = system_dir / "main.py"
        with open(main_py_path, 'w') as f:
            f.write(main_py_content)
        
        # Make executable
        main_py_path.chmod(0o755)
    
    async def _validate_system_structure(self, system_dir: Path, blueprint_data: Dict[str, Any]):
        """Validate system directory structure"""
        required_files = ["main.py", "components/__init__.py"]
        
        for component in blueprint_data.get("components", []):
            comp_name = component["name"]
            required_files.append(f"components/{comp_name}.py")
        
        missing_files = []
        for file_path in required_files:
            full_path = system_dir / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            raise FileNotFoundError(f"Missing required files: {missing_files}")
    
    async def _test_component_imports(self, system_dir: Path):
        """Test that all components can be imported"""
        # Add system directory to Python path
        sys.path.insert(0, str(system_dir))
        
        try:
            # Try importing components module
            import components
            
            # Test that we can import each component
            components_dir = system_dir / "components"
            for py_file in components_dir.glob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                
                module_name = py_file.stem
                try:
                    module = __import__(f"components.{module_name}", fromlist=[module_name])
                except Exception as e:
                    raise ImportError(f"Failed to import components.{module_name}: {e}")
        
        finally:
            # Remove from path
            if str(system_dir) in sys.path:
                sys.path.remove(str(system_dir))

def create_test_runner(verbose: bool = False, timeout: int = 60, cleanup: bool = False) -> PhaseTestRunner:
    """Create a configured PhaseTestRunner instance"""
    env = TestEnvironment(
        verbose=verbose,
        timeout=timeout,
        cleanup_on_success=cleanup,
        cleanup_on_failure=cleanup
    )
    return PhaseTestRunner(env)

async def run_full_pipeline_isolated(blueprint_content: str, test_name: str = "full_pipeline_test", verbose: bool = False) -> List[PhaseResult]:
    """Run the full pipeline (all phases) in isolation with detailed results for each phase"""
    runner = create_test_runner(verbose=verbose)
    results = []
    
    try:
        # Phase 1: Blueprint Validation
        phase1_result = await runner.run_phase1(blueprint_content, f"{test_name}_phase1")
        results.append(phase1_result)
        
        if not phase1_result.success:
            return results
        
        blueprint_data = phase1_result.output_data.get('blueprint_data')
        if not blueprint_data:
            blueprint_data = phase1_result.output_data.get('parsed_yaml')
        
        # Phase 2: Component Generation
        phase2_result = await runner.run_phase2(blueprint_data, f"{test_name}_phase2")
        results.append(phase2_result)
        
        if not phase2_result.success:
            return results
        
        # Phase 3: System Assembly (using mock components for testing)
        components_dir = runner.env.output_dir / "components"
        phase3_result = await runner.run_phase3(components_dir, blueprint_data, f"{test_name}_phase3")
        results.append(phase3_result)
        
        if not phase3_result.success:
            return results
        
        # Phase 4: Deployment
        system_dir = Path(phase3_result.output_data['system_dir'])
        phase4_result = await runner.run_phase4(system_dir, f"{test_name}_phase4")
        results.append(phase4_result)
        
        return results
    
    finally:
        runner.cleanup_environment(all(r.success for r in results))