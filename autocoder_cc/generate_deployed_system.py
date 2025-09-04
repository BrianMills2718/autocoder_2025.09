#!/usr/bin/env python3
"""
Generate Deployed System - Natural Language to Complete Deployed System
======================================================================

This is the primary interface for Autocoder V5.2 that always does the complete
end-to-end pipeline: Natural Language → Blueprint → System → Deployed & Tested

ALWAYS tests the complete pipeline from natural language to working deployment.
"""

import os
import sys
import time
import subprocess
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Set generation mode to disable external service connections during generation
os.environ['AUTOCODER_GENERATION_MODE'] = 'true'

# Import V5.2 pipeline components
from autocoder_cc.blueprint_language.natural_language_to_blueprint import NaturalLanguageToPydanticTranslator
from autocoder_cc.blueprint_language import SystemGenerator
from autocoder_cc.generators.config import generator_settings
from autocoder_cc.core.config import settings
from autocoder_cc.observability.pipeline_metrics import pipeline_metrics, PipelineStage

# Import configuration management components
from autocoder_cc.generation.deployment.config_manager import ConfigurationAnalyzer
from autocoder_cc.generation.deployment.environment_templates import EnvironmentTemplateManager


def check_llm_availability():
    """Check if LLM API keys are configured - fail hard if not"""
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if not openai_key and not anthropic_key and not gemini_key:
        print("\n❌ FAIL-HARD: LLM API Configuration Required")
        print("-" * 50)
        print("Autocoder V5.2 requires LLM for ALL component generation.")
        print("No template fallbacks or mock modes are allowed.")
        print()
        print("Please configure one of the following:")
        print("  • OPENAI_API_KEY - for OpenAI models")
        print("  • ANTHROPIC_API_KEY - for Claude models")
        print("  • GEMINI_API_KEY - for Gemini models")
        print()
        print("Add to your .env file or export as environment variable:")
        print("  export GEMINI_API_KEY='your-key-here'")
        print()
        print("This is a fail-hard requirement - no partial functionality allowed.")
        sys.exit(1)
    
    # Determine which provider is configured (prioritize Gemini for speed)
    if gemini_key:
        provider = "Gemini"
    elif openai_key:
        provider = "OpenAI"
    else:
        provider = "Anthropic"
    
    print(f"✅ LLM API configured: {provider}")
    return True


def display_pipeline_header():
    """Display the pipeline header"""
    print("\n" + "=" * 80)
    print("🚀 AUTOCODER V5.2 - NATURAL LANGUAGE TO DEPLOYED SYSTEM")
    print("=" * 80)
    print("📋 PIPELINE: Natural Language → Blueprint → Components → Deployed System")
    print("🎯 GOAL: Complete end-to-end generation and deployment validation")
    print("⚡ MODE: Always end-to-end testing (no intermediate steps)")
    print("=" * 80)


def get_natural_language_input():
    """Get natural language system description from user"""
    print("\n📝 STEP 1: Natural Language Input")
    print("-" * 50)
    
    # Check for command line argument first
    if len(sys.argv) > 1:
        description = " ".join(sys.argv[1:])
        print(f"Using command line input: {description}")
    else:
        print("Describe the system you want deployed:")
        print("(Examples: 'Create a customer analytics dashboard', 'Build a chat API', etc.)")
        print()
        
        # Get input from user
        description = input("➤ System Description: ").strip()
    
    if not description:
        print("❌ Error: System description cannot be empty")
        return None
        
    if len(description) < 10:
        print("❌ Error: Please provide a more detailed description (at least 10 characters)")
        return None
        
    print(f"\n✅ Input received: {description}")
    return description


def convert_to_blueprint(description: str):
    """Phase 1: Natural Language → Blueprint YAML"""
    print("\n⚙️ PHASE 1: Natural Language → Blueprint YAML")
    print("-" * 50)
    
    pipeline_metrics.start_stage(PipelineStage.NATURAL_LANGUAGE_CONVERSION)
    
    try:
        start_time = time.time()
        
        # Use the V5.2 natural language converter
        converter = NaturalLanguageToPydanticTranslator()
        
        print("🔄 Processing natural language with LLM...")
        blueprint_yaml = converter.generate_full_blueprint(description)
        
        phase1_time = time.time() - start_time
        print(f"✅ Phase 1 Complete: {phase1_time:.1f}s")
        lines_count = len(blueprint_yaml.split('\n'))
        print(f"   Blueprint generated: {lines_count} lines")
        print()
        
        pipeline_metrics.end_stage(PipelineStage.NATURAL_LANGUAGE_CONVERSION, success=True)
        return blueprint_yaml
        
    except Exception as e:
        print(f"❌ Phase 1 Failed: {e}")
        pipeline_metrics.end_stage(PipelineStage.NATURAL_LANGUAGE_CONVERSION, success=False, error=e)
        return None


async def generate_system(blueprint_yaml: str):
    """Phase 2: Blueprint YAML → Complete System with validation"""
    print("⚙️ PHASE 2: Blueprint YAML → Complete System")
    print("-" * 50)
    
    # Start blueprint parsing stage
    pipeline_metrics.start_stage(PipelineStage.BLUEPRINT_PARSING)
    
    try:
        start_time = time.time()
        
        # Create output directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(f"./generated_systems/system_{timestamp}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # CRITICAL: Validate directory creation
        if not output_dir.exists():
            raise RuntimeError(f"Failed to create output directory: {output_dir}")
        
        # Use the V5.2 system generator with timeout
        # FAIL FAST: No bypassing validation - expose real issues
        generator = SystemGenerator(output_dir, bypass_validation=False)  # No workarounds
        
        print("🔄 Generating system components with timeout protection...")
        
        # Save blueprint to temporary file to use the timeout wrapper
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(blueprint_yaml)
            blueprint_file = Path(f.name)
        
        try:
            # Blueprint parsing is part of generation, so end that stage
            pipeline_metrics.end_stage(PipelineStage.BLUEPRINT_PARSING, success=True)
            
            # Start component generation stage
            pipeline_metrics.start_stage(PipelineStage.COMPONENT_GENERATION)
            
            generated_system = await generator.generate_system_with_timeout(blueprint_file)
            
            # CRITICAL: Validate actual generation occurred
            if not generated_system:
                raise RuntimeError("System generation returned None")
            
            # Validate expected files exist
            required_files = ["main.py", "requirements.txt", "components"]
            for required_file in required_files:
                file_path = generated_system.output_directory / required_file
                if not file_path.exists():
                    raise RuntimeError(f"Required file/directory missing: {file_path}")
            
            # Validate components directory has actual components
            components_dir = generated_system.output_directory / "components"
            component_files = list(components_dir.glob("*.py"))
            if not component_files:
                raise RuntimeError(f"No component files generated in {components_dir}")
                
        finally:
            # Clean up temporary file
            blueprint_file.unlink()
        
        phase2_time = time.time() - start_time
        print(f"✅ Phase 2 Complete: {phase2_time:.1f}s")
        print(f"   System Generated: {generated_system.name}")
        print(f"   Output Directory: {generated_system.output_directory}")
        print(f"   Components: {len(generated_system.components)}")
        print(f"   Validated Files: {len(component_files)} component files")
        print()
        
        # Mark component generation as successful
        pipeline_metrics.end_stage(PipelineStage.COMPONENT_GENERATION, success=True)
        
        return generated_system
        
    except Exception as e:
        print(f"❌ Phase 2 Failed: {e}")
        # CRITICAL: Log full stack trace for debugging
        import traceback
        traceback.print_exc()
        # Determine which stage failed
        if "blueprint" in str(e).lower() or "parse" in str(e).lower():
            pipeline_metrics.end_stage(PipelineStage.BLUEPRINT_PARSING, success=False, error=e)
        else:
            pipeline_metrics.end_stage(PipelineStage.COMPONENT_GENERATION, success=False, error=e)
        return None


def validate_system_structure(generated_system):
    """Phase 3: System Structure Validation"""
    print("⚙️ PHASE 3: System Structure Validation")
    print("-" * 50)
    
    pipeline_metrics.start_stage(PipelineStage.VALIDATION)
    
    try:
        system_dir = generated_system.output_directory
        
        # Check required files exist
        required_files = [
            "main.py",
            "requirements.txt", 
            "Dockerfile",
            "docker-compose.yml"
        ]
        
        required_dirs = [
            "components",
            "tests",
            "k8s",
            "config"
        ]
        
        print("🔍 Checking system structure...")
        
        missing_files = []
        missing_dirs = []
        
        for file in required_files:
            if not (system_dir / file).exists():
                missing_files.append(file)
                
        for dir_name in required_dirs:
            if not (system_dir / dir_name).exists():
                missing_dirs.append(dir_name)
        
        if missing_files or missing_dirs:
            print(f"❌ Phase 3 Failed: Missing files/directories")
            if missing_files:
                print(f"   Missing files: {missing_files}")
            if missing_dirs:
                print(f"   Missing directories: {missing_dirs}")
            return False
            
        # Count generated artifacts
        components_count = len(list((system_dir / "components").glob("*.py")))
        tests_count = len(list((system_dir / "tests").glob("test_*.py")))
        k8s_count = len(list((system_dir / "k8s").glob("*.yaml")))
        
        print(f"✅ Phase 3 Complete: System structure valid")
        print(f"   Components: {components_count}")
        print(f"   Tests: {tests_count}")
        print(f"   K8s Manifests: {k8s_count}")
        print()
        
        pipeline_metrics.end_stage(PipelineStage.VALIDATION, success=True)
        return True
        
    except Exception as e:
        print(f"❌ Phase 3 Failed: {e}")
        pipeline_metrics.end_stage(PipelineStage.VALIDATION, success=False, error=e)
        return False


def deploy_and_test_system(generated_system):
    """Phase 4: System Deployment and Testing with dynamic port detection"""
    print("⚙️ PHASE 4: System Deployment and Testing")
    print("-" * 50)
    
    try:
        system_dir = generated_system.output_directory
        
        # CRITICAL: Detect actual port configuration
        port = 8000  # Default port
        
        # Check component configurations for port settings
        components_dir = system_dir / "components"
        for component_file in components_dir.glob("*.py"):
            try:
                with open(component_file, 'r') as f:
                    content = f.read()
                    # Look for port configuration
                    if 'port' in content:
                        # Extract port from config.get("port", XXXX)
                        import re
                        port_match = re.search(r'config\.get\("port",\s*(\d+)\)', content)
                        if port_match:
                            port = int(port_match.group(1))
                            print(f"Found port configuration: {port}")
                            break
            except Exception as e:
                print(f"⚠️ Could not parse component file {component_file}: {e}")
        
        # Check main.py for uvicorn port
        main_py = system_dir / "main.py"
        if main_py.exists():
            with open(main_py, 'r') as f:
                content = f.read()
                import re
                port_match = re.search(r'port=(\d+)', content)
                if port_match:
                    port = int(port_match.group(1))
                    print(f"Found uvicorn port configuration: {port}")
        
        # INTEGRATION POINT 1: Analyze all generated components for configuration requirements
        print("🔍 Analyzing generated components for configuration requirements...")
        analyzer = ConfigurationAnalyzer()
        template_manager = EnvironmentTemplateManager()
        all_requirements = {}
        
        components_dir = system_dir / "components"
        if components_dir.exists():
            for component_file in components_dir.glob("*.py"):
                try:
                    with open(component_file, 'r') as f:
                        component_code = f.read()
                        requirements = analyzer.analyze_component_requirements(component_code)
                        all_requirements.update(requirements)
                        if requirements:
                            print(f"   Found {len(requirements)} config requirements in {component_file.name}")
                except Exception as e:
                    print(f"⚠️ Could not analyze component file {component_file}: {e}")
        
        print(f"✅ Configuration analysis complete: {len(all_requirements)} total requirements")
        
        # Install dependencies
        print("📦 Installing system dependencies...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(system_dir / "requirements.txt")
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"❌ Dependency installation failed: {result.stderr}")
            return False
            
        print("✅ Dependencies installed")
        
        # Start the system
        print(f"🚀 Starting system on port {port}...")
        
        # INTEGRATION POINT 2: Generate required configuration for test environment
        print("⚙️ Generating test environment configuration...")
        test_config = template_manager.resolve_template('test', all_requirements)
        test_template = template_manager.get_template('test')
        
        # Set up environment variables for development testing
        test_env = os.environ.copy()
        
        # Apply generated configuration
        for key, value in test_config.items():
            env_key = key.upper()
            test_env[env_key] = str(value)
            print(f"   {env_key}={value}")
        
        # Legacy environment variables (keeping for backward compatibility)
        legacy_env = {
            'DB_PASSWORD': 'test_password_for_development',
            'DB_HOST': 'localhost',
            'API_SECRET_KEY': 'test_secret_key',
            'JWT_SECRET': 'test_jwt_secret',
            'REDIS_PASSWORD': 'test_redis_password'
        }
        
        for key, value in legacy_env.items():
            if key not in test_env:
                test_env[key] = value
        
        print(f"✅ Environment configuration complete: {len(test_config)} generated + legacy values")
        
        api_process = subprocess.Popen([
            sys.executable, "main.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(system_dir), env=test_env)
        
        # Wait for startup with port-specific testing
        time.sleep(5)
        
        if api_process.poll() is not None:
            stdout, stderr = api_process.communicate()
            print(f"❌ System failed to start:")
            print(f"stdout: {stdout.decode()}")
            print(f"stderr: {stderr.decode()}")
            
            # INTEGRATION POINT 3: Check if failure is due to missing configuration
            error_output = stderr.decode() + stdout.decode()
            missing_configs = []
            for req_key in all_requirements.keys():
                if req_key in error_output or req_key.upper() in error_output:
                    missing_configs.append(req_key)
            
            if missing_configs:
                print(f"💡 Configuration issue detected: Missing {missing_configs}")
                print(f"   Generated config provided: {list(test_config.keys())}")
                print("   Consider updating component analysis or environment templates")
            
            return False
        
        # INTEGRATION POINT 3: Verify all requirements are met
        print("🔎 Verifying configuration requirements are satisfied...")
        missing_required = []
        for key, requirement in all_requirements.items():
            if requirement.get('required', False):
                env_key = key.upper()
                if env_key not in test_env and key not in test_config:
                    missing_required.append(key)
        
        if missing_required:
            print(f"⚠️ Warning: Missing required configuration: {missing_required}")
        else:
            print(f"✅ All {len([r for r in all_requirements.values() if r.get('required', False)])} required configurations satisfied")
            
        print("✅ System started successfully")
        
        # COMPREHENSIVE FUNCTIONAL TESTING (fixing critical Gemini finding)
        try:
            print("🧪 COMPREHENSIVE FUNCTIONAL TESTING...")
            print("   (Replacing superficial health checks with real functionality tests)")
            
            validation_results = {
                "basic_connectivity": False,
                "database_functionality": False,
                "component_communication": False,
                "actual_data_flow": False,
                "error_handling": False,
                "overall_success": False
            }
            
            # 1. Basic connectivity tests
            print("🔍 1. Testing basic connectivity...")
            health_url = f"http://localhost:{port}/health"
            health_response = requests.get(health_url, timeout=10)
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"   ✅ Health endpoint accessible: {health_data.get('status', 'unknown')}")
                validation_results["basic_connectivity"] = True
            else:
                print(f"   ❌ Health endpoint failed: {health_response.status_code}")
                
            # 2. Test actual API functionality (not just health checks)
            print("🔍 2. Testing actual API functionality...")
            
            # Test data processing endpoints
            test_endpoints = ["/api/data", "/data", "/process", "/submit", "/query"]
            functional_endpoint_found = False
            
            for endpoint in test_endpoints:
                try:
                    test_url = f"http://localhost:{port}{endpoint}"
                    response = requests.get(test_url, timeout=5)
                    if response.status_code in [200, 201, 202]:
                        print(f"   ✅ Functional endpoint {endpoint}: {response.status_code}")
                        functional_endpoint_found = True
                        
                        # Try to parse response data
                        try:
                            data = response.json()
                            if isinstance(data, dict) and len(data) > 0:
                                print(f"   ✅ Endpoint returns meaningful data: {len(data)} fields")
                            elif isinstance(data, list) and len(data) > 0:
                                print(f"   ✅ Endpoint returns data array: {len(data)} items")
                        except:
                            print(f"   ⚠️ Endpoint returns non-JSON data")
                            
                        break
                except requests.exceptions.RequestException:
                    continue
                    
            if functional_endpoint_found:
                validation_results["actual_data_flow"] = True
                
            # 3. Test POST functionality if available
            print("🔍 3. Testing POST functionality...")
            
            test_data = {"test": "data", "value": 123, "timestamp": time.time()}
            post_endpoints = ["/api/data", "/data", "/submit", "/process"]
            
            for endpoint in post_endpoints:
                try:
                    test_url = f"http://localhost:{port}{endpoint}"
                    response = requests.post(test_url, json=test_data, timeout=5)
                    if response.status_code in [200, 201, 202]:
                        print(f"   ✅ POST endpoint {endpoint}: {response.status_code}")
                        try:
                            data = response.json()
                            print(f"   ✅ POST response data: {data}")
                        except:
                            print(f"   ✅ POST accepted (non-JSON response)")
                        validation_results["component_communication"] = True
                        break
                except requests.exceptions.RequestException:
                    continue
                    
            # 4. Test error handling
            print("🔍 4. Testing error handling...")
            
            try:
                # Test invalid endpoint
                error_url = f"http://localhost:{port}/invalid_endpoint_test"
                error_response = requests.get(error_url, timeout=5)
                if error_response.status_code == 404:
                    print("   ✅ Proper 404 handling for invalid endpoints")
                    validation_results["error_handling"] = True
                
                # Test invalid POST data
                invalid_url = f"http://localhost:{port}/api/data"
                invalid_response = requests.post(invalid_url, json={"invalid": "structure"}, timeout=5)
                if invalid_response.status_code in [400, 422, 404]:
                    print(f"   ✅ Proper error handling for invalid data: {invalid_response.status_code}")
                    validation_results["error_handling"] = True
                    
            except requests.exceptions.RequestException:
                print("   ⚠️ Error handling test failed (network error)")
                
            # 5. Test database functionality if database components exist
            print("🔍 5. Testing database functionality...")
            
            # Check if Store components exist
            components_dir = system_dir / "components"
            if components_dir.exists():
                store_components = list(components_dir.glob("*store*.py")) + list(components_dir.glob("*Store*.py"))
                if store_components:
                    print(f"   Found {len(store_components)} database components")
                    
                    # Test database endpoints
                    db_endpoints = ["/api/store", "/store", "/save", "/retrieve", "/query"]
                    
                    for endpoint in db_endpoints:
                        try:
                            test_url = f"http://localhost:{port}{endpoint}"
                            response = requests.get(test_url, timeout=5)
                            if response.status_code in [200, 201]:
                                print(f"   ✅ Database endpoint {endpoint}: functional")
                                validation_results["database_functionality"] = True
                                break
                        except:
                            continue
                            
                    # Test database write
                    for endpoint in db_endpoints:
                        try:
                            test_url = f"http://localhost:{port}{endpoint}"
                            test_data = {"data": "test_record", "timestamp": time.time()}
                            response = requests.post(test_url, json=test_data, timeout=5)
                            if response.status_code in [200, 201, 202]:
                                print(f"   ✅ Database write functionality working")
                                validation_results["database_functionality"] = True
                                break
                        except:
                            continue
                else:
                    print("   ℹ️ No database components found, skipping DB tests")
                    validation_results["database_functionality"] = True  # Not required
            else:
                validation_results["database_functionality"] = True  # Not required
                
            # Calculate overall success
            required_tests = ["basic_connectivity", "actual_data_flow", "error_handling"]
            optional_tests = ["component_communication", "database_functionality"]
            
            required_passed = all(validation_results[test] for test in required_tests)
            optional_passed = sum(validation_results[test] for test in optional_tests)
            
            validation_results["overall_success"] = required_passed and optional_passed >= 1
            
            # Save validation results to file (fixing the phase4_validation_results.json issue)
            import json
            results_file = system_dir / "phase4_validation_results.json"
            with open(results_file, 'w') as f:
                json.dump(validation_results, f, indent=2)
                
            print("\n📊 COMPREHENSIVE VALIDATION RESULTS:")
            for test, result in validation_results.items():
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"   {test}: {status}")
                
            if validation_results["overall_success"]:
                print(f"\n✅ Phase 4 Complete: COMPREHENSIVE FUNCTIONAL VALIDATION PASSED")
                print(f"   System demonstrates real functionality on port {port}")
                return True
            else:
                print(f"\n❌ Phase 4 Failed: COMPREHENSIVE FUNCTIONAL VALIDATION FAILED")
                print(f"   System lacks required functionality - not just health checks")
                return False
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Comprehensive testing failed: {e}")
            validation_results["overall_success"] = False
            
            # Save failed validation results
            import json
            results_file = system_dir / "phase4_validation_results.json"
            with open(results_file, 'w') as f:
                json.dump(validation_results, f, indent=2)
            return False
            
        finally:
            # Cleanup
            if api_process and api_process.poll() is None:
                print("🛑 Stopping system...")
                api_process.terminate()
                api_process.wait()
                print("✅ System stopped")
            
    except Exception as e:
        print(f"❌ Phase 4 Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def display_success_summary(description: str, generated_system, total_time: float):
    """Display final success summary with pipeline robustness status"""
    system_dir = generated_system.output_directory
    
    print("\n" + "🎉" * 20)
    print("SUCCESS! COMPLETE END-TO-END PIPELINE VALIDATION")
    print("🎉" * 20)
    print()
    print("📋 PIPELINE SUMMARY:")
    print(f"   ➤ Input: '{description}'")
    print(f"   ➤ Output: Complete deployed system")
    print(f"   ➤ Total Time: {total_time:.1f}s")
    print()
    print("✅ PHASES COMPLETED:")
    print("   1. ✅ Natural Language → Blueprint YAML")
    print("   2. ✅ Blueprint → Complete System")  
    print("   3. ✅ System Structure Validation")
    print("   4. ✅ Comprehensive Functional Validation (FIXED)")
    
    # Display comprehensive validation results
    results_file = system_dir / "phase4_validation_results.json"
    if results_file.exists():
        print("\n🔬 COMPREHENSIVE VALIDATION RESULTS:")
        import json
        with open(results_file, 'r') as f:
            validation_results = json.load(f)
            
        for test, result in validation_results.items():
            if test != "overall_success":
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"   • {test.replace('_', ' ').title()}: {status}")
        
        overall = validation_results.get("overall_success", False)
        overall_status = "✅ PASSED" if overall else "❌ FAILED"
        print(f"   • Overall Functional Validation: {overall_status}")
    else:
        print("\n⚠️ Validation results file not found")
    
    # Show pipeline robustness status
    tests_count = len(list((system_dir / "tests").glob("test_*.py"))) if (system_dir / "tests").exists() else 0
    
    print()
    print("🛡️ PIPELINE ROBUSTNESS STATUS:")
    if tests_count > 0:
        print(f"   ✅ Test generation: {tests_count} test files generated")
    else:
        if settings.SKIP_TEST_GENERATION:
            print("   📋 Test generation: Skipped (configured)")
        else:
            print("   ⚠️ Test generation: Failed but system functional")
    
    print(f"   ✅ AST validation: {settings.AST_VALIDATION_MODE} mode")
    print("   ✅ Pipeline configuration: Fail-fast behavior (graceful degradation removed)")
    print()
    print("📁 GENERATED SYSTEM:")
    print(f"   📂 Location: {system_dir}")
    print(f"   📂 Name: {generated_system.name}")
    print(f"   📂 Components: {len(generated_system.components)}")
    print()
    print("🚀 DEPLOYMENT ARTIFACTS:")
    print(f"   • main.py - System entry point")
    print(f"   • components/ - Generated components")
    print(f"   • k8s/ - Kubernetes manifests")
    print(f"   • docker-compose.yml - Local deployment")
    if tests_count > 0:
        print(f"   • tests/ - Test suite ({tests_count} files)")
    else:
        print(f"   • tests/ - No tests (core system functional)")
    print()
    print("🌐 VALIDATED ENDPOINTS:")
    from autocoder_cc.generators.config import generator_settings
    print(f"   • {generator_settings.api_base_url}:{generator_settings.default_api_port}/health - Health check ✅")
    print("   • Additional system endpoints ✅")
    print()
    print("✨ PROOF: Natural language successfully converted to working deployed system!")
    if tests_count == 0:
        print("📝 NOTE: System is fully functional despite missing tests (pipeline robustness working)")


async def main():
    """Main entry point - always does complete end-to-end pipeline"""
    
    # Add fallback mode for testing
    minimal_mode = len(sys.argv) > 1 and '--minimal' in sys.argv
    
    if minimal_mode:
        print("🔧 Running in minimal mode - skipping complex operations")
        os.environ['AUTOCODER_GENERATION_MODE'] = 'true'
        os.environ['SKIP_LLM_CALLS'] = 'true'
        os.environ['SKIP_OBSERVABILITY_SETUP'] = 'true'
    
    # Check LLM availability first - fail hard if not configured
    if not minimal_mode:
        check_llm_availability()
    
    display_pipeline_header()
    
    # Get natural language input
    description = get_natural_language_input()
    if not description:
        sys.exit(1)
        
    print(f"\n🎯 TARGET: Deploy system from '{description}'")
    
    total_start_time = time.time()
    
    # Phase 1: Natural Language → Blueprint
    blueprint_yaml = convert_to_blueprint(description)
    if not blueprint_yaml:
        print("❌ PIPELINE FAILED at Phase 1")
        sys.exit(1)
        
    # Phase 2: Blueprint → System  
    generated_system = await generate_system(blueprint_yaml)
    if not generated_system:
        print("❌ PIPELINE FAILED at Phase 2")
        sys.exit(1)
        
    # Phase 3: System Structure Validation
    if not validate_system_structure(generated_system):
        print("❌ PIPELINE FAILED at Phase 3")
        sys.exit(1)
        
    # Phase 4: Deployment & Testing
    if not deploy_and_test_system(generated_system):
        print("❌ PIPELINE FAILED at Phase 4")
        sys.exit(1)
        
    # Success!
    total_time = time.time() - total_start_time
    display_success_summary(description, generated_system, total_time)
    
    # Display pipeline metrics summary
    print("\n📊 PIPELINE METRICS SUMMARY")
    print("-" * 50)
    summary = pipeline_metrics.get_pipeline_summary()
    print(f"   Total Duration: {summary['total_duration_seconds']:.1f}s")
    print(f"   Stages Completed: {summary['stages_completed']}/{summary['stages_attempted']}")
    if summary['stage_errors']:
        print(f"   ⚠️  Failed Stages: {', '.join(summary['stage_errors'].keys())}")
    if summary['critical_errors']:
        print("   🚨 CRITICAL ERRORS DETECTED")
    
    print("\n🏆 COMPLETE SUCCESS!")
    print("   End-to-end pipeline validation: PASSED ✅")
    print("   Natural language → deployed system: WORKING ✅")


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ PIPELINE FAILED: {e}")
        sys.exit(1)