#!/usr/bin/env python3
"""
Validation Gate - Component-by-Component Testing Integration
Blocks system generation until all components pass validation

This implements the "block early, block often" philosophy by integrating
component testing directly into the system generation pipeline.
"""
import anyio
import importlib.util
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import ast
import astor

from autocoder_cc.tests.tools.real_component_test_runner import RealComponentTestRunner as ComponentTestRunner, ComponentTestConfig, ComponentTestResult
from .component_name_utils import find_best_class_name_match, generate_class_name_variants
from autocoder_cc.healing.ast_transformers.message_envelope_transformer import MessageEnvelopeTransformer
from autocoder_cc.healing.ast_transformers.communication_method_transformer import CommunicationMethodTransformer
from .adaptive_test_generator import AdaptiveTestDataGenerator


@dataclass
class ValidationGateResult:
    """Result of validation gate check"""
    gate_passed: bool
    total_components: int
    passed_components: int
    failed_components: int
    blocking_failures: List[str]
    detailed_results: List[ComponentTestResult]
    can_proceed_to_generation: bool


class ComponentValidationGate:
    """
    Validation gate that blocks system generation until all components pass testing.
    
    This gate is inserted into the system generation pipeline to ensure:
    1. All components are tested in isolation before integration
    2. Contract validation passes (inheritance, method signatures, async patterns)
    3. Functional validation passes (lifecycle, input/output processing)
    4. Clear blame assignment when failures occur
    5. No system generation proceeds until ALL components pass
    """
    
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode  # If True, ANY failure blocks generation
        self.component_test_runner = ComponentTestRunner()  # Now using RealComponentTestRunner without mocks
    
    def _apply_ast_transformers(self, component_file: Path) -> bool:
        """Apply AST transformers to fix common patterns before validation"""
        try:
            with open(component_file, 'r') as f:
                code = f.read()
            
            # First fix common syntax issues before parsing
            code = self._fix_common_syntax_issues(code)
            
            # Parse the code
            tree = ast.parse(code)
            
            # Apply transformers in sequence
            transformers = [
                MessageEnvelopeTransformer(),
                CommunicationMethodTransformer()
            ]
            
            for transformer in transformers:
                tree = transformer.visit(tree)
            
            # Convert back to code
            fixed_code = astor.to_source(tree)
            
            # Inject cleanup method if missing
            fixed_code = self._inject_cleanup_if_missing_in_code(fixed_code)
            
            # Write back to file
            with open(component_file, 'w') as f:
                f.write(fixed_code)
            
            print(f"✅ Applied AST transformers to {component_file.name}")
            return True
        except Exception as e:
            print(f"⚠️ Failed to apply transformers to {component_file.name}: {e}")
            return False
    
    def _fix_common_syntax_issues(self, code: str) -> str:
        """Fix common syntax issues before AST parsing"""
        lines = code.split('\n')
        fixed_lines = []
        seen_init = False
        in_class = False
        
        for line in lines:
            # Detect class definition
            if line.strip().startswith('class '):
                in_class = True
                seen_init = False
                fixed_lines.append(line)
            # Skip duplicate __init__ methods
            elif in_class and '    def __init__(' in line:
                if not seen_init:
                    seen_init = True
                    fixed_lines.append(line)
                else:
                    # Skip duplicate __init__
                    print(f"  Removing duplicate __init__ method")
                    # Skip lines until next method or class
                    continue
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _inject_cleanup_if_missing_in_code(self, code: str) -> str:
        """Inject cleanup method if missing in the code"""
        try:
            # Check if cleanup exists
            if 'def cleanup(' in code or 'async def cleanup(' in code:
                return code
            
            # Parse to find classes
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it inherits from ComposedComponent
                    for base in node.bases:
                        if isinstance(base, ast.Name) and 'Component' in base.id:
                            # Find insertion point (after last method)
                            lines = code.split('\n')
                            class_indent = ''
                            class_line = -1
                            
                            for i, line in enumerate(lines):
                                if f'class {node.name}' in line:
                                    class_line = i
                                    # Get class indentation
                                    class_indent = line[:len(line) - len(line.lstrip())]
                                    break
                            
                            if class_line >= 0:
                                # Find last method in class
                                last_method_line = class_line
                                for i in range(class_line + 1, len(lines)):
                                    if lines[i].strip().startswith('def ') or lines[i].strip().startswith('async def '):
                                        last_method_line = i
                                    elif lines[i].strip() and not lines[i].startswith(' '):
                                        # End of class
                                        break
                                
                                # Find end of last method
                                insertion_line = last_method_line + 1
                                for i in range(last_method_line + 1, len(lines)):
                                    if lines[i].strip() and not lines[i].startswith(' '):
                                        insertion_line = i
                                        break
                                    elif lines[i].strip().startswith('def ') or lines[i].strip().startswith('async def '):
                                        insertion_line = i
                                        break
                                
                                # Insert cleanup method
                                cleanup_method = f'''
{class_indent}    async def cleanup(self):
{class_indent}        """Cleanup method for component lifecycle"""
{class_indent}        pass
'''
                                lines.insert(insertion_line, cleanup_method)
                                code = '\n'.join(lines)
                                print(f"  Injected cleanup() method")
                                return code
            
            return code
            
        except Exception as e:
            print(f"  Could not inject cleanup: {e}")
            return code
    
    def _import_component_safely(self, component_file: Path):
        """Safely import a component with proper path handling"""
        # Store original path
        original_path = sys.path.copy()
        
        # Add component directory to path for local imports
        sys.path.insert(0, str(component_file.parent))
        
        try:
            spec = importlib.util.spec_from_file_location(
                component_file.stem, 
                component_file
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
            else:
                print(f"Could not create module spec for {component_file}")
                return None
        except Exception as e:
            print(f"Failed to import {component_file}: {e}")
            return None
        finally:
            # Restore original path
            sys.path = original_path
    
    async def validate_components_for_system_generation(self, 
                                                      components_dir: Path,
                                                      system_name: str) -> ValidationGateResult:
        """
        Run complete component validation before allowing system generation.
        
        Args:
            components_dir: Directory containing generated component files
            system_name: Name of the system being generated
            
        Returns:
            ValidationGateResult with gate pass/fail status and detailed results
        """
        
        print(f"🚦 VALIDATION GATE: Testing components for system '{system_name}'")
        print(f"   Components directory: {components_dir}")
        print(f"   Strict mode: {self.strict_mode}")
        
        # Apply AST transformers to all components before validation
        print("📝 Applying AST transformers to fix communication patterns...")
        for component_file in components_dir.glob("*.py"):
            if component_file.name not in ['__init__.py', 'observability.py', 'communication.py', 'manifest.yaml']:
                self._apply_ast_transformers(component_file)
        
        # Create test configurations for all components
        test_configs = self._create_test_configs_from_components(components_dir)
        
        if not test_configs:
            return ValidationGateResult(
                gate_passed=False,
                total_components=0,
                passed_components=0,
                failed_components=0,
                blocking_failures=["No components found to validate"],
                detailed_results=[],
                can_proceed_to_generation=False
            )
        
        print(f"   Found {len(test_configs)} components to validate")
        
        # Run component test suite
        test_results = await self.component_test_runner.run_component_test_suite(test_configs)
        
        # Convert list of results to summary dict
        test_summary = self._create_test_summary(test_results)
        
        # Analyze results for gate decision
        gate_result = self._analyze_gate_result(test_summary, system_name)
        
        # Log gate decision
        if gate_result.can_proceed_to_generation:
            print(f"✅ VALIDATION GATE PASSED: System generation allowed for '{system_name}'")
        else:
            print(f"🚫 VALIDATION GATE FAILED: System generation blocked for '{system_name}'")
            for failure in gate_result.blocking_failures:
                print(f"   ❌ {failure}")
        
        return gate_result
    
    def _create_test_configs_from_components(self, components_dir: Path) -> List[ComponentTestConfig]:
        """Create test configurations for all components in directory"""
        
        configs = []
        
        if not components_dir.exists():
            return configs
        
        for component_file in components_dir.glob("*.py"):
            if component_file.name.startswith("__"):
                continue
            
            # Skip non-component infrastructure files
            if component_file.name in ["communication.py", "observability.py", "manifest.yaml"]:
                continue
            
            # Detect component class and type
            component_info = self._analyze_component_file(component_file)
            
            if component_info:
                # Create appropriate test inputs based on component type
                test_inputs = self._generate_test_inputs_for_component_type(
                    component_file, 
                    component_info["type"]
                )
                expected_outputs = len(test_inputs)  # Expect 1:1 transformation by default
                
                config = ComponentTestConfig(
                    component_path=component_file,
                    component_class_name=component_info["class_name"],
                    test_inputs=test_inputs,
                    expected_outputs=expected_outputs,
                    timeout_seconds=10.0,
                    validate_contract=True,
                    validate_functionality=True,
                    validate_performance=False  # Optional for now
                )
                configs.append(config)
        
        return configs
    
    def _analyze_component_file(self, component_file: Path) -> Optional[Dict[str, str]]:
        """Analyze component file to extract class name and type with robust name matching"""
        
        try:
            import ast
            
            with open(component_file, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Extract the expected component name from the file name
            expected_component_name = component_file.stem  # Remove .py extension
            
            # Collect all class definitions
            all_classes = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it inherits from Component or specific base classes
                    base_classes = []
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            base_classes.append(base.id)
                        elif isinstance(base, ast.Attribute):
                            base_classes.append(base.attr)
                    
                    # Determine component type
                    component_type = "Component"  # Default
                    
                    # Check if it inherits from known component types
                    component_base_classes = ["Component", "Source", "Sink", "Transformer", "Model", "Store", 
                                            "APIEndpoint", "HarnessComponent", "ComposedComponent",
                                            "ComposedComponent", "Controller", "StreamProcessor", "WebSocket",
                                            "Router", "Aggregator", "Filter", "Accumulator"]
                    
                    has_component_inheritance = any(base in component_base_classes for base in base_classes)
                    
                    # Only include classes that inherit from component base classes
                    if has_component_inheritance:
                        for base in base_classes:
                            if base in ["Source", "Sink", "Transformer", "Model", "Store", "APIEndpoint", 
                                       "Controller", "StreamProcessor", "WebSocket"]:
                                component_type = base
                                break
                        else:
                            component_type = "Component"  # Default for ComposedComponent etc
                        
                        all_classes[node.name] = component_type
                    # Skip classes that don't inherit from component base classes (like ComponentCommunicator)
            
            if not all_classes:
                return None
            
            # Find the best matching class name using robust matching
            available_class_names = set(all_classes.keys())
            best_match = find_best_class_name_match(available_class_names, expected_component_name)
            
            # Return information for the best matched class
            return {
                "class_name": best_match,
                "type": all_classes.get(best_match, "Component"),
                "file": component_file.name,
                "all_classes_found": list(all_classes.keys()),
                "expected_name": expected_component_name
            }
        
        except Exception as e:
            print(f"Warning: Could not analyze component file {component_file}: {e}")
        
        return None
    
    def _generate_test_inputs_for_component_type(self, component_file: Path, 
                                                  component_type: str) -> List[Dict[str, Any]]:
        """Generate appropriate test inputs based on component introspection"""
        
        # Try adaptive generation first
        try:
            generator = AdaptiveTestDataGenerator()
            test_inputs = generator.generate_test_data(component_file, num_cases=3)
            
            if test_inputs:
                print(f"  Using adaptive test data ({len(test_inputs)} cases)")
                return test_inputs
        except Exception as e:
            print(f"  Adaptive generation failed: {e}, falling back to defaults")
        
        # Fallback to original type-based generation
        print(f"  Using default test data for {component_type}")
        
        if component_type == "Source":
            # Sources don't need inputs, they generate data
            return [{}]  # Empty input to trigger generation
        
        elif component_type == "Controller":
            # Enhanced controller defaults with action field
            return [
                {"action": "create", "data": {"title": "Test Item 1"}},
                {"action": "read", "id": "test-123"},
                {"action": "list", "filters": {}}
            ]
        
        elif component_type == "Sink":
            # Sinks receive data to output
            return [
                {"id": 1, "value": 10, "data": "test_item_1"},
                {"id": 2, "value": 20, "data": "test_item_2"},
                {"id": 3, "value": 30, "data": "test_item_3"}
            ]
        
        elif component_type == "Transformer":
            # Transformers process data
            return [
                {"id": 1, "value": 10, "raw_data": "transform_me_1"},
                {"id": 2, "value": 20, "raw_data": "transform_me_2"},
                {"id": 3, "value": 30, "raw_data": "transform_me_3"}
            ]
        
        elif component_type == "Model":
            # Models need features for inference
            return [
                {"id": 1, "features": [0.5, 0.3, 0.8], "metadata": {"source": "test"}},
                {"id": 2, "features": [0.2, 0.7, 0.4], "metadata": {"source": "test"}},
                {"id": 3, "features": [0.9, 0.1, 0.6], "metadata": {"source": "test"}}
            ]
        
        elif component_type == "Store":
            # Stores receive data to persist
            return [
                {"id": 1, "record": {"name": "test_record_1", "value": 100}},
                {"id": 2, "record": {"name": "test_record_2", "value": 200}},
                {"id": 3, "record": {"name": "test_record_3", "value": 300}}
            ]
        
        elif component_type == "APIEndpoint":
            # API endpoints receive requests
            return [
                {"request_id": 1, "endpoint": "/test", "data": {"action": "process", "value": 10}},
                {"request_id": 2, "endpoint": "/test", "data": {"action": "process", "value": 20}},
                {"request_id": 3, "endpoint": "/test", "data": {"action": "process", "value": 30}}
            ]
        
        else:
            # Generic component test data
            return [
                {"test_id": 1, "value": 10, "test_data": "generic_test_1"},
                {"test_id": 2, "value": 20, "test_data": "generic_test_2"},
                {"test_id": 3, "value": 30, "test_data": "generic_test_3"}
            ]
    
    def _create_test_summary(self, test_results: List[ComponentTestResult]) -> Dict[str, Any]:
        """Convert list of test results to summary dict"""
        passed = sum(1 for r in test_results if r.passed)
        failed = sum(1 for r in test_results if not r.passed)
        
        return {
            "total_components": len(test_results),
            "passed": passed,
            "failed": failed,
            "results": test_results
        }
    
    def _analyze_gate_result(self, test_summary: Dict[str, Any], system_name: str) -> ValidationGateResult:
        """Analyze test results to determine if gate should pass"""
        
        total_components = test_summary["total_components"]
        passed_components = test_summary["passed"]
        failed_components = test_summary["failed"]
        
        # Identify blocking failures
        blocking_failures = []
        
        for result in test_summary["results"]:
            if not result.success:
                # Categorize the failure
                failure_type = self._categorize_component_failure(result)
                blocking_failures.append(
                    f"Component '{result.component_name}' failed {failure_type}: {result.error_message}"
                )
        
        # Gate decision logic
        if self.strict_mode:
            # In strict mode, ANY failure blocks generation
            gate_passed = failed_components == 0
        else:
            # In permissive mode, only critical failures block generation
            critical_failures = self._count_critical_failures(test_summary["results"])
            gate_passed = critical_failures == 0
        
        can_proceed = gate_passed and total_components > 0
        
        return ValidationGateResult(
            gate_passed=gate_passed,
            total_components=total_components,
            passed_components=passed_components,
            failed_components=failed_components,
            blocking_failures=blocking_failures,
            detailed_results=test_summary["results"],
            can_proceed_to_generation=can_proceed
        )
    
    def _categorize_component_failure(self, result: ComponentTestResult) -> str:
        """Categorize the type of component failure for blame assignment"""
        
        # Check for placeholder logic error (NotImplementedError)
        if result.error_message and "NotImplementedError" in result.error_message:
            return "PlaceholderLogicError (NotImplementedError raised)"
        
        if not result.contract_validation_passed:
            if result.contract_errors:
                return f"contract violation ({result.contract_errors[0]})"
            else:
                return "contract validation"
        
        elif not result.functional_test_passed:
            if not result.setup_passed or not result.cleanup_passed:
                return "lifecycle failure (setup/cleanup)"
            elif not result.input_processing_passed:
                return "input processing failure"
            elif not result.output_generation_passed:
                return "output generation failure"
            else:
                return "functional validation"
        
        else:
            return "unknown failure"
    
    def _count_critical_failures(self, results: List[ComponentTestResult]) -> int:
        """Count failures that are critical enough to block generation"""
        
        critical_count = 0
        
        for result in results:
            if not result.success:
                # Contract failures are always critical
                if not result.contract_validation_passed:
                    critical_count += 1
                # Lifecycle failures are critical
                elif not result.setup_passed or not result.cleanup_passed:
                    critical_count += 1
                # Input/output failures might be acceptable in permissive mode
                # (component might work in different contexts)
        
        return critical_count
    
    def generate_validation_report(self, gate_result: ValidationGateResult, output_file: Path = None) -> str:
        """Generate detailed validation report"""
        
        report_lines = [
            "# Component Validation Gate Report",
            f"Generated: {anyio.current_time()}",
            "",
            "## Summary",
            f"- Total Components: {gate_result.total_components}",
            f"- Passed: {gate_result.passed_components}",
            f"- Failed: {gate_result.failed_components}",
            f"- Gate Status: {'PASSED' if gate_result.gate_passed else 'FAILED'}",
            f"- Can Proceed: {'YES' if gate_result.can_proceed_to_generation else 'NO'}",
            ""
        ]
        
        if gate_result.blocking_failures:
            report_lines.extend([
                "## Blocking Failures",
                ""
            ])
            for failure in gate_result.blocking_failures:
                report_lines.append(f"- {failure}")
            report_lines.append("")
        
        report_lines.extend([
            "## Detailed Results",
            ""
        ])
        
        for result in gate_result.detailed_results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            report_lines.extend([
                f"### {result.component_name} ({result.component_type}) - {status}",
                f"- Execution Time: {result.execution_time:.2f}s",
                f"- Contract Validation: {'PASS' if result.contract_validation_passed else 'FAIL'}",
                f"- Functional Test: {'PASS' if result.functional_test_passed else 'FAIL'}",
                f"- Harness Compatible: {'YES' if result.harness_compatibility else 'NO'}",
                ""
            ])
            
            if result.error_message:
                report_lines.extend([
                    f"**Error**: {result.error_message}",
                    ""
                ])
        
        report = "\n".join(report_lines)
        
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(report)
        
        return report


class BlameAssignmentAnalyzer:
    """
    Analyzes component test failures to assign clear blame and suggest fixes.
    
    This helps developers understand exactly what went wrong and how to fix it.
    """
    
    def analyze_failure_blame(self, results: List[ComponentTestResult]) -> Dict[str, Any]:
        """Analyze failures and assign blame with suggested fixes"""
        
        blame_analysis = {
            "total_failures": 0,
            "failure_categories": {},
            "suggested_fixes": [],
            "priority_fixes": [],
            "blame_assignment": {}
        }
        
        for result in results:
            if not result.success:
                blame_analysis["total_failures"] += 1
                
                # Categorize failure
                category = self._get_failure_category(result)
                if category not in blame_analysis["failure_categories"]:
                    blame_analysis["failure_categories"][category] = []
                blame_analysis["failure_categories"][category].append(result.component_name)
                
                # Generate specific blame and fix suggestion
                blame_info = self._assign_specific_blame(result)
                blame_analysis["blame_assignment"][result.component_name] = blame_info
                
                if blame_info["suggested_fix"]:
                    blame_analysis["suggested_fixes"].append({
                        "component": result.component_name,
                        "fix": blame_info["suggested_fix"],
                        "priority": blame_info["priority"]
                    })
                    
                    if blame_info["priority"] == "high":
                        blame_analysis["priority_fixes"].append(blame_info["suggested_fix"])
        
        return blame_analysis
    
    def _get_failure_category(self, result: ComponentTestResult) -> str:
        """Get high-level failure category"""
        
        if not result.contract_validation_passed:
            return "contract_violation"
        elif not result.functional_test_passed:
            return "functional_failure"
        else:
            return "unknown_failure"
    
    def _assign_specific_blame(self, result: ComponentTestResult) -> Dict[str, Any]:
        """Assign specific blame and suggest concrete fixes"""
        
        blame_info = {
            "blame_target": "unknown",
            "root_cause": "unknown",
            "suggested_fix": None,
            "priority": "medium"
        }
        
        # Check for placeholder logic error (NotImplementedError) first
        if result.error_message and "NotImplementedError" in result.error_message:
            blame_info.update({
                "blame_target": "llm_generation",
                "root_cause": "LLM generated component with placeholder logic (NotImplementedError)",
                "suggested_fix": f"Regenerate {result.component_name} with complete business logic implementation",
                "priority": "high"
            })
            return blame_info
        
        if not result.contract_validation_passed:
            if not result.required_methods_present:
                blame_info.update({
                    "blame_target": "llm_generation",
                    "root_cause": "LLM did not generate required methods",
                    "suggested_fix": f"Regenerate {result.component_name} with explicit method requirements",
                    "priority": "high"
                })
            elif not result.async_patterns_correct:
                blame_info.update({
                    "blame_target": "llm_generation",
                    "root_cause": "LLM generated sync methods instead of async",
                    "suggested_fix": f"Regenerate {result.component_name} with async method requirements",
                    "priority": "high"
                })
            elif not result.harness_compatibility:
                blame_info.update({
                    "blame_target": "llm_generation",
                    "root_cause": "Component does not inherit from correct base class",
                    "suggested_fix": f"Regenerate {result.component_name} ensuring proper inheritance",
                    "priority": "high"
                })
        
        elif not result.functional_test_passed:
            if not result.lifecycle_methods_work:
                blame_info.update({
                    "blame_target": "component_logic",
                    "root_cause": "Setup or cleanup methods have bugs",
                    "suggested_fix": f"Fix lifecycle methods in {result.component_name}",
                    "priority": "high"
                })
            elif not result.input_processing_works:
                blame_info.update({
                    "blame_target": "component_logic",
                    "root_cause": "Component cannot process input data correctly",
                    "suggested_fix": f"Fix input processing logic in {result.component_name}",
                    "priority": "medium"
                })
            elif not result.output_generation_works:
                blame_info.update({
                    "blame_target": "component_logic",
                    "root_cause": "Component does not generate expected outputs",
                    "suggested_fix": f"Fix output generation logic in {result.component_name}",
                    "priority": "medium"
                })
        
        return blame_info


def main():
    """Test the validation gate"""
    
    print("🚦 Testing Component Validation Gate")
    
    # Test with a sample components directory
    components_dir = Path("./test_generated_systems/simple_test_pipeline/components")
    
    if components_dir.exists():
        gate = ComponentValidationGate(strict_mode=True)
        
        async def test_gate():
            result = await gate.validate_components_for_system_generation(
                components_dir, "test_system"
            )
            
            print(f"\nGate Result:")
            print(f"  Passed: {result.gate_passed}")
            print(f"  Can Proceed: {result.can_proceed_to_generation}")
            print(f"  Components: {result.passed_components}/{result.total_components}")
            
            if result.blocking_failures:
                print(f"  Failures:")
                for failure in result.blocking_failures:
                    print(f"    - {failure}")
            
            # Generate report
            report = gate.generate_validation_report(result)
            print(f"\nValidation Report:\n{report}")
        
        import anyio
        anyio.run(test_gate)
    else:
        print(f"No test components found at {components_dir}")


if __name__ == "__main__":
    main()