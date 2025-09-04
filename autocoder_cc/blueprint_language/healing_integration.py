from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
Healing Integration - Complete Self-Healing Pipeline
Integrates AST-based self-healing with system generation and validation

This creates the complete healing loop:
1. Parse blueprint
2. Generate components 
3. Validate components (validation gate)
4. If validation fails, apply self-healing
5. Re-validate healed components
6. Generate system scaffold if all components pass
7. Retry entire process if healing successful
"""
import anyio
import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from .system_blueprint_parser import SystemBlueprintParser, ParsedSystemBlueprint
from .system_scaffold_generator import SystemScaffoldGenerator
from .integration_validation_gate import IntegrationValidationGate as ComponentValidationGate
from dataclasses import dataclass
from typing import Dict, Any, List

@dataclass
class ValidationGateResult:
    """Placeholder for validation gate result"""
    success: bool
    details: Dict[str, Any] = None
    component_results: List[Any] = None
from .ast_self_healing import SelfHealingSystem, HealingResult
from .llm_component_generator import LLMComponentGenerator, ComponentGenerationError
from autocoder_cc.recipes import RecipeExpander, get_recipe


@dataclass
class HealingPipelineResult:
    """Result of complete healing pipeline execution"""
    success: bool
    system_generated: bool
    healing_attempts: int
    validation_passes: int
    components_healed: int
    
    # Generated system info
    system_name: str
    output_directory: Optional[Path] = None
    
    # Detailed results
    validation_results: List[ValidationGateResult] = None
    healing_results: List[HealingResult] = None
    final_validation: Optional[ValidationGateResult] = None
    
    # Error information
    error_message: Optional[str] = None
    failure_stage: Optional[str] = None
    
    # Performance metrics
    total_execution_time: float = 0.0
    healing_time: float = 0.0
    validation_time: float = 0.0
    generation_time: float = 0.0


class HealingIntegratedGenerator:
    """
    System generator with integrated self-healing capabilities.
    
    This class combines all the Phase 6-7 capabilities:
    - Component-by-component validation
    - AST-based self-healing
    - Validation gates
    - Blame assignment
    - Retry logic
    
    The complete workflow ensures that only systems with fully validated
    components proceed to generation, and any validation failures trigger
    automatic healing attempts.
    """
    
    def __init__(self, 
                 output_dir: Path,
                 max_healing_attempts: int = 3,
                 strict_validation: bool = True,
                 enable_metrics: bool = True):
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_healing_attempts = max_healing_attempts
        self.strict_validation = strict_validation
        self.enable_metrics = enable_metrics
        
        # Initialize subsystems
        self.blueprint_parser = SystemBlueprintParser()
        self.scaffold_generator = SystemScaffoldGenerator(output_dir)
        self.validation_gate = ComponentValidationGate()
        self.healing_system = SelfHealingSystem(max_healing_attempts=max_healing_attempts)
        
        # Initialize recipe expander for primitive-based generation
        self.recipe_expander = RecipeExpander()
        
        # Initialize strict validation pipeline (Phase 4 integration)
        from autocoder_cc.validation.pipeline_integration import StrictValidationPipeline
        self.config_validation_pipeline = StrictValidationPipeline()
        self.enable_config_validation = True  # Feature flag
        
        # Initialize LLM component generator - REQUIRED
        try:
            self.component_generator = LLMComponentGenerator()
        except ComponentGenerationError as e:
            # FAIL FAST - No graceful degradation
            raise RuntimeError(
                f"CRITICAL: LLM component generator initialization failed: {e}. "
                "System cannot function without LLM generation capability. "
                "Ensure LLM provider is configured with valid API key."
            ) from e
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = get_logger("HealingIntegratedGenerator")
    
    async def generate_system_with_healing(self, 
                                         blueprint_yaml: str,
                                         force_regeneration: bool = False) -> HealingPipelineResult:
        """
        Generate system with integrated validation and self-healing.
        
        This is the main entry point that orchestrates the complete pipeline:
        1. Parse blueprint
        2. Generate/validate components with healing retry loop
        3. Generate system scaffold when all components pass
        """
        
        start_time = time.time()
        
        result = HealingPipelineResult(
            success=False,
            system_generated=False,
            healing_attempts=0,
            validation_passes=0,
            components_healed=0,
            system_name="unknown",
            validation_results=[],
            healing_results=[]
        )
        
        try:
            self.logger.info("🚀 Starting integrated system generation with healing")
            
            # 1. Parse blueprint
            self.logger.info("📋 Parsing system blueprint...")
            parse_start = time.time()
            
            parsed_blueprint = self.blueprint_parser.parse_string(blueprint_yaml)
            result.system_name = parsed_blueprint.system.name
            
            parse_time = time.time() - parse_start
            self.logger.info(f"   Blueprint parsed in {parse_time:.2f}s")
            
            # 2. Setup system output directory
            system_output_dir = self.output_dir / parsed_blueprint.system.name
            system_output_dir.mkdir(parents=True, exist_ok=True)
            result.output_directory = system_output_dir
            
            # 3. Component generation and validation with healing loop
            self.logger.info("🔧 Starting component generation and validation loop...")
            healing_start = time.time()
            
            components_ready, validation_final = await self._component_healing_loop(
                parsed_blueprint, system_output_dir, result
            )
            
            result.healing_time = time.time() - healing_start
            result.final_validation = validation_final
            
            if not components_ready:
                result.failure_stage = "component_validation_and_healing"
                result.error_message = "Components failed validation even after healing attempts"
                return result
            
            # 4. Generate system scaffold
            self.logger.info("🏗️ Generating system scaffold...")
            generation_start = time.time()
            
            scaffold = self.scaffold_generator.generate_system(
                parsed_blueprint, enable_metrics=self.enable_metrics
            )
            
            result.generation_time = time.time() - generation_start
            result.system_generated = True
            
            # 5. Final success
            result.success = True
            result.total_execution_time = time.time() - start_time
            
            self.logger.info(f"✅ System generation completed successfully!")
            self.logger.info(f"   Total time: {result.total_execution_time:.2f}s")
            self.logger.info(f"   System: {result.system_name}")
            self.logger.info(f"   Output: {result.output_directory}")
            
        except Exception as e:
            import traceback
            result.failure_stage = "pipeline_error"
            result.error_message = str(e)
            result.total_execution_time = time.time() - start_time
            self.logger.error(f"💥 Pipeline failed: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
        
        return result
    
    async def _component_healing_loop(self, 
                                    parsed_blueprint: ParsedSystemBlueprint,
                                    system_output_dir: Path,
                                    result: HealingPipelineResult) -> Tuple[bool, Optional[ValidationGateResult]]:
        """
        Execute the component generation + validation + healing loop.
        
        This loop continues until either:
        1. All components pass validation (success)
        2. Max healing attempts reached (failure)
        3. No healing fixes can be applied (failure)
        """
        
        components_dir = system_output_dir / "components"
        components_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate observability.py BEFORE component generation so components can import from it
        await self._generate_observability_before_components(system_output_dir, parsed_blueprint)
        
        for attempt in range(self.max_healing_attempts + 1):  # +1 for initial attempt
            self.logger.info(f"\n🔄 Component validation attempt {attempt + 1}")
            
            # Generate components if first attempt or if healing was applied
            if attempt == 0 or result.healing_results:
                self.logger.info("   🔧 Generating components...")
                await self._generate_components(parsed_blueprint, components_dir)
            
            # ALWAYS validate components - NO BYPASSING
            # Validate components
            self.logger.info("   🚦 Running validation gate...")
            validation_start = time.time()
            
            # Get the integration validation result
            integration_result = await self.validation_gate.validate_system(
                components_dir, parsed_blueprint.system.name
            )
            
            # Convert IntegrationValidationResult to ValidationGateResult for compatibility
            validation_result = ValidationGateResult(
                success=integration_result.can_proceed,
                details={
                    "system_name": integration_result.system_name,
                    "total_components": integration_result.total_components,
                    "passed_components": integration_result.passed_components,
                    "failed_components": integration_result.failed_components,
                    "success_rate": integration_result.success_rate,
                    "raw_details": integration_result.details
                },
                component_results=[]
            )
            
            # Store additional properties for later access
            validation_result.can_proceed = integration_result.can_proceed
            validation_result.failed_components = integration_result.failed_components
            validation_result.passed_components = integration_result.passed_components
            validation_result.total_components = integration_result.total_components
            validation_result.success_rate = integration_result.success_rate
            
            result.validation_time += time.time() - validation_start
            result.validation_passes += 1
            result.validation_results.append(validation_result)
            
            # Check if validation passed
            if validation_result.can_proceed:
                self.logger.info("   ✅ All components passed validation!")
                return True, validation_result
            
            # If this was the last attempt, don't try healing
            if attempt >= self.max_healing_attempts:
                self.logger.error("   ❌ Max healing attempts reached")
                return False, validation_result
            
            # Attempt healing
            self.logger.info(f"   🚨 {validation_result.failed_components} components failed - attempting healing...")
            result.healing_attempts += 1
            
            healing_success, healing_results = await self.healing_system.heal_and_validate_components(
                components_dir, parsed_blueprint.system.name
            )
            
            result.healing_results.extend(healing_results)
            result.components_healed += len([r for r in healing_results if r.healing_successful])
            
            # Check for circuit breaker activations and other loop conditions
            circuit_breaker_activated = any(
                "Circuit breaker activated" in (r.error_message or "") 
                for r in healing_results
            )
            
            no_progress_detected = any(
                "No progress detected" in (r.error_message or "")
                for r in healing_results
            )
            
            definitive_failures = [
                r for r in healing_results 
                if "DEFINITIVE FAILURE" in (r.error_message or "") or
                   "Maximum healing attempts reached" in (r.error_message or "")
            ]
            
            if circuit_breaker_activated:
                self.logger.warning("   ⚡ Circuit breaker activated for one or more components")
            
            if no_progress_detected:
                self.logger.warning("   🔄 No progress detected in some components - potential healing loops")
            
            if definitive_failures:
                self.logger.error(f"   ❌ {len(definitive_failures)} components have definitive failures:")
                for failure in definitive_failures:
                    self.logger.error(f"      - {failure.component_name}: {failure.error_message}")
            
            if not healing_success:
                self.logger.error("   ❌ Healing failed - cannot fix component issues")
                if circuit_breaker_activated:
                    self.logger.error("   ⚡ Some components exceeded max healing attempts")
                if no_progress_detected:
                    self.logger.error("   🔄 Some components stuck in healing loops")
                return False, validation_result
            
            self.logger.info(f"   🔧 Healing applied - retrying validation...")
        
        # Final summary if we exhausted all attempts
        self.logger.error(f"   ❌ Exhausted all {self.max_healing_attempts} healing attempts without success")
        self.logger.error("   Summary of issues:")
        failed_components = set()
        for healing_result in result.healing_results:
            if not healing_result.healing_successful or not healing_result.validation_passed_after_healing:
                failed_components.add(healing_result.component_name)
        for component in failed_components:
            self.logger.error(f"      - {component}: Could not be healed successfully")
        
        return False, None
    
    async def _generate_components(self, 
                                 parsed_blueprint: ParsedSystemBlueprint, 
                                 components_dir: Path) -> None:
        """Generate component files from parsed blueprint"""
        
        self.logger.info(f"   Generating {len(parsed_blueprint.system.components)} components...")
        
        # Convert blueprint for validation pipeline
        blueprint_dict = parsed_blueprint.raw_blueprint if hasattr(parsed_blueprint, 'raw_blueprint') else {}
        
        for component in parsed_blueprint.system.components:
            component_file = components_dir / f"{component.name.lower()}.py"
            
            if not component_file.exists():
                try:
                    # Phase 4: Validate and heal component config before generation
                    component_config = {}
                    if hasattr(component, 'config'):
                        component_config = component.config
                    elif hasattr(component, 'configuration'):
                        component_config = component.configuration
                    
                    if self.enable_config_validation:
                        try:
                            validated_config = await self.config_validation_pipeline.validate_and_heal_or_fail(
                                component_name=component.name,
                                component_type=component.type,
                                config=component_config,
                                blueprint=blueprint_dict
                            )
                            # Update component config with validated/healed version
                            component_config = validated_config
                            if hasattr(component, 'config'):
                                component.config = validated_config
                            elif hasattr(component, 'configuration'):
                                component.configuration = validated_config
                            self.logger.info(f"     ✅ Config validated/healed for {component.name}")
                        except Exception as e:
                            self.logger.error(f"     ❌ Config validation failed for {component.name}: {e}")
                            if self.strict_validation:
                                raise
                            # Continue with original config if not in strict mode
                    
                    # Check if this component type has a recipe
                    recipe = None
                    recipe_info = None
                    try:
                        recipe = get_recipe(component.type)
                        recipe_info = self.recipe_expander.get_recipe_info(component.type)
                    except ValueError:
                        # No recipe for this component type - that's OK
                        pass
                    
                    if recipe:
                        # CRITICAL FIX: Use recipe for structure but LLM for implementation
                        # Recipes should provide the skeleton, not hardcoded stub implementations
                        self.logger.info(f"     Using recipe '{component.type}' structure with LLM implementation for {component.name}")
                        
                        # Get the recipe structure to guide LLM
                        recipe_info = self.recipe_expander.get_recipe_info(component.type)
                        
                        # Fall through to LLM generation with recipe guidance
                        # DO NOT skip LLM generation - we need real implementations!
                        self.logger.info(f"     Recipe provides structure, LLM will generate implementation...")
                    
                    if self.component_generator:
                        # Use LLM to generate real component code
                        self.logger.info(f"     Generating {component.name} with LLM...")
                        
                        # Enhance description with recipe information if available
                        enhanced_description = component.description
                        if recipe:
                            # Add recipe context to help LLM generate proper implementation
                            enhanced_description = (
                                f"{component.description}. "
                                f"This is a {component.type} component based on {recipe_info['base_primitive']} primitive. "
                                f"IMPORTANT: Generate REAL WORKING IMPLEMENTATION with actual data storage, "
                                f"not stub methods. For Store components, use at minimum an in-memory dictionary "
                                f"to actually persist data between calls."
                            )
                        
                        # Convert component to format expected by LLM generator
                        component_dict = {
                            'name': component.name,
                            'type': component.type,
                            'description': enhanced_description,
                            'inputs': [{'name': i.name, 'schema': i.schema} for i in component.inputs] if hasattr(component, 'inputs') else [],
                            'outputs': [{'name': o.name, 'schema': o.schema} for o in component.outputs] if hasattr(component, 'outputs') else [],
                            'config': component_config  # Already validated/healed above
                        }
                        
                        # Generate component code using LLM with timeout protection
                        try:
                            component_code = await asyncio.wait_for(
                                self.component_generator.generate_component_implementation(
                                    component_type=component.type,
                                    component_name=component.name,
                                    component_description=enhanced_description,
                                    component_config=component_dict.get('config', {}),
                                    class_name=component.name.replace('_', '').title()
                                ),
                                timeout=120.0  # 2-minute timeout for component generation
                            )
                        except asyncio.TimeoutError:
                            self.logger.error(f"⏰ Component {component.name} generation timed out after 120 seconds")
                            # Continue with next component instead of failing entire system
                            continue
                    else:
                        # FAIL HARD - NO FALLBACKS
                        raise ComponentGenerationError(
                            f"LLM component generator not available for {component.name}. "
                            f"System requires working LLM provider for component generation. "
                            f"Check API keys and provider configuration."
                        )
                    
                    # Write component file directly - wrapping already added all imports
                    with open(component_file, 'w') as f:
                        # Component code already has all necessary imports from wrap_component_with_boilerplate
                        f.write(component_code)
                    
                    self.logger.info(f"     Generated: {component.name}")
                    
                except Exception as e:
                    # FAIL FAST with detailed debugging information
                    import traceback
                    import os
                    error_details = f"""
❌ COMPONENT GENERATION FAILED - CANNOT CONTINUE

Component Details:
  Name: {component.name}
  Type: {component.type}
  Description: {component.description or 'No description'}
  
Error Information:
  Error Type: {type(e).__name__}
  Error Message: {str(e)}
  
Stack Trace:
{traceback.format_exc()}

Debug Information:
  Component file path: {component_file}
  Component generator available: {self.component_generator is not None}
  Output directory exists: {components_dir.exists()}
  Write permissions: {os.access(str(components_dir), os.W_OK) if components_dir.exists() else False}
  
System cannot continue with incomplete component generation.
Fix the root cause before proceeding.
"""
                    self.logger.error(error_details)
                    
                    # FAIL FAST - Don't produce broken systems
                    raise ComponentGenerationError(
                        f"Failed to generate component {component.name}: {str(e)}"
                    ) from e
        
        # Create __init__.py files after component generation
        # Use the parent directory of components_dir to get the system output directory
        system_output_dir = components_dir.parent
        self._create_package_init_files(system_output_dir, parsed_blueprint)
        
        # Generate observability module for components to import
        self._copy_supporting_files(system_output_dir, parsed_blueprint)
    
    def generate_pipeline_report(self, result: HealingPipelineResult, output_file: Path = None) -> str:
        """Generate comprehensive pipeline execution report"""
        
        report_lines = [
            "# Healing Integrated Generation Report",
            f"Generated: {time.time()}",
            "",
            "## Pipeline Summary",
            f"- System Name: {result.system_name}",
            f"- Success: {result.success}",
            f"- System Generated: {result.system_generated}",
            f"- Total Execution Time: {result.total_execution_time:.2f}s",
            ""
        ]
        
        if result.output_directory:
            report_lines.append(f"- Output Directory: {result.output_directory}")
            report_lines.append("")
        
        # Performance breakdown
        report_lines.extend([
            "## Performance Breakdown",
            f"- Validation Time: {result.validation_time:.2f}s",
            f"- Healing Time: {result.healing_time:.2f}s", 
            f"- Generation Time: {result.generation_time:.2f}s",
            ""
        ])
        
        # Healing summary
        report_lines.extend([
            "## Healing Summary",
            f"- Healing Attempts: {result.healing_attempts}",
            f"- Validation Passes: {result.validation_passes}",
            f"- Components Healed: {result.components_healed}",
            ""
        ])
        
        # Validation results
        if result.validation_results:
            report_lines.extend([
                "## Validation Results",
                ""
            ])
            
            for i, validation in enumerate(result.validation_results):
                report_lines.extend([
                    f"### Validation Pass {i + 1}",
                    f"- Components: {getattr(validation, 'passed_components', 0)}/{getattr(validation, 'total_components', 0)}",
                    f"- Gate Passed: {validation.success if hasattr(validation, 'success') else getattr(validation, 'can_proceed', False)}",
                    f"- Can Proceed: {getattr(validation, 'can_proceed', False)}",
                    ""
                ])
                
                if hasattr(validation, 'blocking_failures') and validation.blocking_failures:
                    report_lines.append("**Blocking Failures:**")
                    for failure in validation.blocking_failures:
                        report_lines.append(f"- {failure}")
                    report_lines.append("")
        
        # Healing results
        if result.healing_results:
            report_lines.extend([
                "## Healing Results",
                ""
            ])
            
            for healing in result.healing_results:
                status = "✅ SUCCESS" if healing.healing_successful else "❌ FAILED"
                report_lines.extend([
                    f"### {healing.component_name} - {status}",
                    f"- Fixes Applied: {len(healing.fixes_applied)}",
                    ""
                ])
        
        # Error information
        if not result.success:
            report_lines.extend([
                "## Failure Information",
                f"- Failure Stage: {result.failure_stage}",
                f"- Error Message: {result.error_message}",
                ""
            ])
        
        report = "\n".join(report_lines)
        
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(report)
        
        return report
    
    def _create_package_init_files(self, output_dir: Path, parsed_blueprint: ParsedSystemBlueprint):
        """Create necessary __init__.py files for proper Python package structure"""
        
        # Create scaffolds/__init__.py (top level)
        scaffolds_dir = output_dir / "scaffolds"
        if scaffolds_dir.exists():
            scaffolds_init = scaffolds_dir / "__init__.py"
            with open(scaffolds_init, 'w', encoding='utf-8') as f:
                f.write('"""Generated system scaffolds"""')
        
        # Find the system directory (should be scaffolds/system_name)
        system_dir = None
        if scaffolds_dir.exists():
            for system_child in scaffolds_dir.iterdir():
                if system_child.is_dir():
                    system_dir = system_child
                    break
        
        if not system_dir:
            self.logger.warning("Could not find system directory for creating __init__.py files")
            return
        
        # Create main system __init__.py
        main_init = system_dir / "__init__.py"
        with open(main_init, 'w', encoding='utf-8') as f:
            f.write(f'''"""
Generated system: {parsed_blueprint.system.name}
{parsed_blueprint.system.description or "Generated by Autocoder with Healing Integration"}
"""

__version__ = "{parsed_blueprint.system.version}"
__system_name__ = "{parsed_blueprint.system.name}"
''')
        
        # Create components/__init__.py with component imports  
        components_dir = system_dir / "components"
        if components_dir.exists():
            components_init = components_dir / "__init__.py"
            
            # Generate imports for all components
            imports = []
            supported_types = {"Source", "Transformer", "Sink", "Model", "Store", "APIEndpoint", "Accumulator", "Router", "Controller", "StreamProcessor", "MessageBus", "WebSocket", "Aggregator", "Filter"}
            
            for component in parsed_blueprint.system.components:
                if component.type in supported_types:
                    class_name = f"Generated{component.type}_{component.name}"
                    imports.append(f"from .{component.name} import {class_name}")
            
            # Build the __all__ list
            all_imports = [f"Generated{component.type}_{component.name}" for component in parsed_blueprint.system.components if component.type in supported_types]
            
            init_content = f'''"""
Component imports for {parsed_blueprint.system.name}
Generated by Autocoder Healing Integration
"""

{chr(10).join(imports)}

__all__ = {all_imports}
'''
            
            with open(components_init, 'w', encoding='utf-8') as f:
                f.write(init_content)
            
            self.logger.info(f"✅ Created package structure with __init__.py files")
            self.logger.info(f"   - Scaffolds: {scaffolds_dir / '__init__.py'}")
            self.logger.info(f"   - Main: {main_init}")  
            self.logger.info(f"   - Components: {components_init} (with {len(imports)} imports)")

    async def _generate_observability_before_components(self, system_output_dir: Path, parsed_blueprint: ParsedSystemBlueprint):
        """Generate observability.py BEFORE component generation so components can import from it"""
        
        self.logger.info("🔍 VERIFICATION: _generate_observability_before_components method called")
        self.logger.info(f"🔍 VERIFICATION: System output directory: {system_output_dir}")
        self.logger.info(f"🔍 VERIFICATION: System name: {parsed_blueprint.system.name}")
        
        # Components directory should already exist at this point
        components_dir = system_output_dir / "components"
        self.logger.info(f"🔍 VERIFICATION: Components dir exists: {components_dir.exists()}")
        
        if not components_dir.exists():
            self.logger.error(f"Components directory does not exist: {components_dir}")
            return
        
        # Generate observability.py using ObservabilityGenerator
        self.logger.info("🔍 VERIFICATION: About to generate observability.py BEFORE component generation")
        from autocoder_cc.generators.scaffold.observability_generator import ObservabilityGenerator
        
        generator = ObservabilityGenerator()
        observability_content = generator.generate_observability_module(
            system_name=parsed_blueprint.system.name,
            include_prometheus=True
        )
        self.logger.info(f"🔍 VERIFICATION: Generated content length: {len(observability_content)}")
        
        # Write observability.py to components directory
        observability_file = components_dir / "observability.py"
        self.logger.info(f"🔍 VERIFICATION: Writing to: {observability_file}")
        
        with open(observability_file, 'w', encoding='utf-8') as f:
            f.write(observability_content)
        
        self.logger.info(f"🔍 VERIFICATION: File created: {observability_file.exists()}")
        if observability_file.exists():
            self.logger.info(f"🔍 VERIFICATION: File size: {observability_file.stat().st_size} bytes")
        
        self.logger.info(f"✅ Generated observability.py BEFORE components: {observability_file}")

    def _copy_supporting_files(self, output_dir: Path, parsed_blueprint: ParsedSystemBlueprint):
        """Copy essential supporting files to generated system"""
        import shutil
        
        self.logger.info("🔍 VERIFICATION: _copy_supporting_files method called")
        self.logger.info(f"🔍 VERIFICATION: Output directory: {output_dir}")
        self.logger.info(f"🔍 VERIFICATION: System name: {parsed_blueprint.system.name}")
        
        # Find the system directory (should be scaffolds/system_name)
        scaffolds_dir = output_dir / "scaffolds"
        self.logger.info(f"🔍 VERIFICATION: Scaffolds dir exists: {scaffolds_dir.exists()}")
        
        system_dir = None
        if scaffolds_dir.exists():
            for system_child in scaffolds_dir.iterdir():
                if system_child.is_dir():
                    system_dir = system_child
                    self.logger.info(f"🔍 VERIFICATION: Found system dir: {system_dir}")
                    break
        
        if not system_dir:
            self.logger.warning("Could not find system directory for copying supporting files")
            return
            
        components_dir = system_dir / "components"
        self.logger.info(f"🔍 VERIFICATION: Components dir exists: {components_dir.exists()}")
        if not components_dir.exists():
            self.logger.warning(f"Components directory does not exist: {components_dir}")
            return
        
        # Generate observability.py using ObservabilityGenerator
        self.logger.info("🔍 VERIFICATION: About to generate observability.py")
        from autocoder_cc.generators.scaffold.observability_generator import ObservabilityGenerator
        
        generator = ObservabilityGenerator()
        observability_content = generator.generate_observability_module(
            system_name=parsed_blueprint.system.name,
            include_prometheus=True
        )
        self.logger.info(f"🔍 VERIFICATION: Generated content length: {len(observability_content)}")
        
        # Write observability.py to components directory
        observability_file = components_dir / "observability.py"
        self.logger.info(f"🔍 VERIFICATION: Writing to: {observability_file}")
        
        with open(observability_file, 'w', encoding='utf-8') as f:
            f.write(observability_content)
        
        self.logger.info(f"🔍 VERIFICATION: File created: {observability_file.exists()}")
        if observability_file.exists():
            self.logger.info(f"🔍 VERIFICATION: File size: {observability_file.stat().st_size} bytes")
        
        self.logger.info(f"✅ Generated observability.py: {observability_file}")


async def main():
    """Test the healing integrated generator"""
    
    print("🚀 Testing Healing Integrated Generator")
    
    # Sample blueprint for testing
    test_blueprint = """
system:
  name: test_healing_pipeline
  description: Test system for healing integration
  
  components:
    - name: data_source
      type: Source
      description: Test data generator
      outputs:
        - name: data
          schema: DataRecord
          
    - name: data_processor
      type: Transformer
      description: Data processor
      inputs:
        - name: input
          schema: DataRecord
      outputs:
        - name: output
          schema: ProcessedData
          
    - name: data_sink
      type: Sink
      description: Data collector
      inputs:
        - name: input
          schema: ProcessedData
  
  bindings:
    - from: data_source.data
      to: data_processor.input
    - from: data_processor.output
      to: data_sink.input
"""
    
    # Create generator
    generator = HealingIntegratedGenerator(
        output_dir=Path("./healing_test_output"),
        max_healing_attempts=2,
        strict_validation=True
    )
    
    # Run generation with healing
    result = await generator.generate_system_with_healing(test_blueprint)
    
    print(f"\\nGeneration Result:")
    print(f"  Success: {result.success}")
    print(f"  System Generated: {result.system_generated}")
    print(f"  Healing Attempts: {result.healing_attempts}")
    print(f"  Components Healed: {result.components_healed}")
    print(f"  Total Time: {result.total_execution_time:.2f}s")
    
    if result.output_directory:
        print(f"  Output: {result.output_directory}")
    
    if result.error_message:
        print(f"  Error: {result.error_message}")
    
    # Generate report
    report = generator.generate_pipeline_report(result)
    print(f"\\nPipeline Report:\\n{report}")


if __name__ == "__main__":
    import anyio
    anyio.run(main)


# SystemGenerator Adapter - Drop-in replacement for broken SystemGenerator
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

@dataclass
class GeneratedSystem:
    """Match the original SystemGenerator's return type"""
    name: str
    output_directory: Path
    components: List[Dict[str, Any]]
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemRequirements:
    """Compatibility class for enhanced_system_generator"""
    name: str = ""
    description: str = ""
    components: List[Dict[str, Any]] = field(default_factory=list)
    performance_targets: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DecisionAudit:
    """Compatibility class for enhanced_system_generator"""
    timestamp: str = ""
    decision: str = ""
    rationale: str = ""
    alternatives: List[str] = field(default_factory=list)

@dataclass  
class TransparentAnalysis:
    """Compatibility class for enhanced_system_generator"""
    decisions: List[DecisionAudit] = field(default_factory=list)
    benchmarks_used: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0

@dataclass
class SystemGenerationReport:
    """Compatibility class for enhanced_system_generator"""
    system: GeneratedSystem = None
    analysis: TransparentAnalysis = None
    requirements: SystemRequirements = None
    success: bool = False
    errors: List[str] = field(default_factory=list)

class SystemGenerator:
    """
    Drop-in replacement for the original SystemGenerator.
    This IS SystemGenerator now - powered by HealingIntegratedGenerator.
    
    Maintains 100% interface compatibility while using the working
    healing/validation pipeline internally.
    """
    
    def __init__(self, output_dir: Path, skip_deployment: bool = True, 
                 bypass_validation: bool = False, verbose: bool = True,
                 timeout: Optional[int] = None):
        """Match original SystemGenerator constructor exactly"""
        self.output_dir = Path(output_dir)
        self.skip_deployment = skip_deployment
        self.bypass_validation = bypass_validation
        self.verbose = verbose
        self.timeout = timeout
        
        # Internal: Use HealingIntegratedGenerator
        self._healing_gen = HealingIntegratedGenerator(
            output_dir=output_dir,
            max_healing_attempts=3,
            strict_validation=not bypass_validation,
            enable_metrics=True
        )
        
        # Match original's logger attribute
        self.logger = self._healing_gen.logger
        
    async def generate_system_from_yaml(self, blueprint_yaml: str) -> GeneratedSystem:
        """
        Generate system from YAML - exact same interface as original.
        
        Args:
            blueprint_yaml: Blueprint in YAML format
            
        Returns:
            GeneratedSystem object matching original's structure
            
        Raises:
            Same exceptions as original for compatibility
        """
        try:
            # Use healing generator
            result = await self._healing_gen.generate_system_with_healing(
                blueprint_yaml,
                force_regeneration=False
            )
            
            if not result.success:
                # Match original's error behavior
                raise RuntimeError(
                    f"System generation failed: {result.error_message}\n"
                    f"Stage: {result.failure_stage}\n"
                    f"Healing attempts: {result.healing_attempts}"
                )
            
            # Extract component list from generated files
            components = []
            if result.output_directory and result.output_directory.exists():
                components_dir = result.output_directory / "components"
                if components_dir.exists():
                    for comp_file in components_dir.glob("*.py"):
                        components.append({
                            "name": comp_file.stem,
                            "file": str(comp_file),
                            "type": "generated"
                        })
            
            # Return compatible object
            return GeneratedSystem(
                name=result.system_name,
                output_directory=result.output_directory,
                components=components,
                version="1.0.0",
                metadata={
                    "generator": "HealingIntegratedGenerator",
                    "healing_attempts": result.healing_attempts,
                    "components_healed": result.components_healed,
                    "generation_time": result.total_execution_time
                }
            )
            
        except Exception as e:
            # Log and re-raise to match original behavior
            if hasattr(self, 'logger'):
                self.logger.error(f"Generation failed: {e}")
            raise
    
    async def generate_system(self, blueprint_path: str, output_path: str) -> Dict[str, Any]:
        """
        Generate system from file path - for compatibility with service interface.
        """
        # Read blueprint file
        with open(blueprint_path, 'r') as f:
            blueprint_yaml = f.read()
        
        # Ensure output path matches
        self.output_dir = Path(output_path)
        self._healing_gen.output_dir = Path(output_path)
        
        # Generate system
        result = await self.generate_system_from_yaml(blueprint_yaml)
        
        # Return dict format for interface compatibility
        return {
            "success": True,
            "system_name": result.name,
            "output_directory": str(result.output_directory),
            "components": result.components,
            "metadata": result.metadata
        }
    
    def validate_system(self, system_config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate system configuration - synchronous for compatibility.
        """
        errors = []
        
        # Basic validation to match original
        if "system" not in system_config and "components" not in system_config:
            errors.append("Invalid blueprint structure: missing 'system' or 'components'")
        
        if not system_config.get("components") and not system_config.get("system", {}).get("components"):
            errors.append("No components defined in blueprint")
        
        return (len(errors) == 0, errors)