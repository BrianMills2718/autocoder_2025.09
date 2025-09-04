"""
Generator Factory - Allows switching between SystemGenerator and HealingIntegratedGenerator.

This factory pattern enables instant rollback between generation pipelines
by setting the AUTOCODER_GENERATOR environment variable:
- "legacy" or unset: Use original SystemGenerator
- "healing": Use new HealingIntegratedGenerator

Rollback is as simple as: export AUTOCODER_GENERATOR=legacy
"""

import os
from pathlib import Path
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


def get_generator(output_dir: Path, skip_deployment: bool = True):
    """
    Get the appropriate generator based on configuration.
    
    This is our rollback mechanism - just change the env var!
    
    Args:
        output_dir: Directory for generated output
        skip_deployment: Whether to skip Kubernetes deployment generation
        
    Returns:
        Either SystemGenerator or HealingIntegratedGenerator instance
        
    Environment Variables:
        AUTOCODER_GENERATOR: Controls which generator to use
            - "legacy" or unset: SystemGenerator (default)
            - "healing": HealingIntegratedGenerator
    """
    generator_type = os.environ.get("AUTOCODER_GENERATOR", "legacy").lower()
    
    logger.info(f"Generator factory: Using {generator_type} generator")
    
    if generator_type == "legacy":
        # Use original SystemGenerator
        from autocoder_cc.blueprint_language import SystemGenerator
        logger.info("Loading SystemGenerator (legacy pipeline)")
        return SystemGenerator(output_dir, skip_deployment=skip_deployment)
        
    elif generator_type == "healing":
        # Use new HealingIntegratedGenerator
        from autocoder_cc.blueprint_language.healing_integration import HealingIntegratedGenerator
        logger.info("Loading HealingIntegratedGenerator (new healing pipeline)")
        return HealingIntegratedGeneratorAdapter(output_dir, skip_deployment=skip_deployment)
        
    else:
        # Unknown type - default to legacy for safety
        logger.warning(f"Unknown generator type '{generator_type}', defaulting to legacy")
        from autocoder_cc.blueprint_language import SystemGenerator
        return SystemGenerator(output_dir, skip_deployment=skip_deployment)


class HealingIntegratedGeneratorAdapter:
    """
    Adapter to make HealingIntegratedGenerator compatible with SystemGenerator interface.
    
    This allows drop-in replacement without changing calling code.
    """
    
    def __init__(self, output_dir: Path, skip_deployment: bool = True):
        """Initialize the adapter with a HealingIntegratedGenerator."""
        from autocoder_cc.blueprint_language.healing_integration import HealingIntegratedGenerator
        
        self.output_dir = output_dir
        self.skip_deployment = skip_deployment
        self.generator = HealingIntegratedGenerator(
            output_dir=output_dir,
            max_healing_attempts=3,
            strict_validation=True,
            enable_metrics=True
        )
        self.logger = logger
        
    async def generate_system_from_yaml(self, blueprint_yaml: str) -> Any:
        """
        Generate system from YAML blueprint.
        
        Adapts HealingIntegratedGenerator's generate_system_with_healing
        to match SystemGenerator's generate_system_from_yaml interface.
        """
        self.logger.info("Generating system using HealingIntegratedGenerator")
        
        # Call the healing generator
        result = await self.generator.generate_system_with_healing(
            blueprint_yaml, 
            force_regeneration=False
        )
        
        if not result.success:
            # Convert healing failure to exception for compatibility
            error_msg = (
                f"Generation failed at stage: {result.failure_stage}\n"
                f"Error: {result.error_message}\n"
                f"Healing attempts: {result.healing_attempts}\n"
                f"Components healed: {result.components_healed}"
            )
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Return a compatible result object
        # SystemGenerator returns a GeneratedSystem object
        # We'll create a simple compatible object
        class GeneratedSystemCompat:
            def __init__(self, name, output_dir, components):
                self.name = name
                self.output_directory = output_dir
                self.components = components
                
        return GeneratedSystemCompat(
            name=result.system_name,
            output_dir=result.output_directory,
            components=[]  # TODO: Extract component list from result if needed
        )
    
    def __getattr__(self, name):
        """
        Delegate any other method calls to the underlying generator.
        
        This ensures compatibility with any other SystemGenerator methods.
        """
        return getattr(self.generator, name)


def get_generator_info() -> dict:
    """
    Get information about the current generator configuration.
    
    Returns:
        Dictionary with generator type and configuration details
    """
    generator_type = os.environ.get("AUTOCODER_GENERATOR", "legacy").lower()
    
    return {
        "type": generator_type,
        "class": "SystemGenerator" if generator_type == "legacy" else "HealingIntegratedGenerator",
        "healing_enabled": generator_type == "healing",
        "rollback_command": "export AUTOCODER_GENERATOR=legacy" if generator_type == "healing" else None,
        "switch_command": "export AUTOCODER_GENERATOR=healing" if generator_type == "legacy" else None,
    }


def print_generator_status():
    """Print the current generator status for debugging."""
    info = get_generator_info()
    
    print("=" * 50)
    print("GENERATOR FACTORY STATUS")
    print("=" * 50)
    print(f"Current Generator: {info['class']}")
    print(f"Type: {info['type']}")
    print(f"Healing Enabled: {info['healing_enabled']}")
    
    if info['rollback_command']:
        print(f"\nTo rollback: {info['rollback_command']}")
    if info['switch_command']:
        print(f"\nTo switch: {info['switch_command']}")
    
    print("=" * 50)


if __name__ == "__main__":
    # Test the factory
    print_generator_status()
    
    # Test getting a generator
    generator = get_generator(Path("./test_output"))
    print(f"\nGenerator instance: {generator.__class__.__name__}")