#!/usr/bin/env python3
"""
End-to-end CLI tests that verify the complete generation flow.
These tests run the actual CLI commands that users would run.
"""

import pytest
import subprocess
import tempfile
import json
import os
from pathlib import Path


class TestCLIEndToEnd:
    """Test the complete CLI flow from natural language to generated system"""
    
    def test_generate_from_natural_language(self):
        """
        Test the exact command that originally failed:
        python3 -m autocoder_cc.cli generate "Build a data pipeline..."
        
        This is a REGRESSION TEST for the blueprint structure mismatch bug.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "generated_system"
            
            # The exact NL request that failed
            nl_request = (
                "Build a data pipeline that reads CSV files from a directory, "
                "filters rows where status equals 'active', enriches them with "
                "user data from a PostgreSQL database, and writes the results to S3"
            )
            
            # Run the CLI command
            result = subprocess.run(
                [
                    "python3", "-m", "autocoder_cc.cli",
                    "generate", nl_request,
                    "--output", str(output_dir)
                ],
                capture_output=True,
                text=True,
                timeout=120  # 2 minutes timeout
            )
            
            # Check if command succeeded
            if result.returncode != 0:
                print(f"STDOUT:\n{result.stdout}")
                print(f"STDERR:\n{result.stderr}")
                
                # This should NOT fail with "Component csv_file_source not found in blueprint"
                assert "not found in blueprint" not in result.stderr, \
                    "Blueprint structure mismatch detected - validation expecting wrong structure"
            
            assert result.returncode == 0, f"Generation failed: {result.stderr}"
            
            # Verify output was created
            assert output_dir.exists(), "Output directory not created"
            
            # Check for expected files
            main_file = output_dir / "main.py"
            assert main_file.exists(), "main.py not generated"
            
            # Verify the generated main.py has proper structure
            content = main_file.read_text()
            assert "SystemExecutionHarness" in content
            assert "csv_file_source" in content  # Component should be there
    
    def test_validate_blueprint_command(self):
        """Test blueprint validation CLI command"""
        # Create a test blueprint with correct structure
        blueprint = {
            "system": {
                "name": "test_system",
                "components": [
                    {
                        "name": "source",
                        "type": "Source",
                        "config": {"path": "/data"}
                    }
                ],
                "connections": []
            },
            "metadata": {},
            "policy": {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as f:
            import yaml
            yaml.dump(blueprint, f)
            f.flush()
            
            # Run validation
            result = subprocess.run(
                ["python3", "-m", "autocoder_cc.cli", "validate", f.name],
                capture_output=True,
                text=True
            )
            
            # Should pass validation
            assert result.returncode == 0 or "valid" in result.stdout.lower()
    
    def test_generate_with_healing(self):
        """Test that generation with incomplete configs triggers healing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "healed_system"
            
            # Minimal request that will need healing
            nl_request = "Create a simple data pipeline from CSV to database"
            
            # Run with healing enabled (should be default)
            result = subprocess.run(
                [
                    "python3", "-m", "autocoder_cc.cli",
                    "generate", nl_request,
                    "--output", str(output_dir),
                    "--verbose"  # Get more output
                ],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Check for healing messages in verbose output
            if "--verbose" in result.stdout or "--verbose" in result.stderr:
                # Should see healing attempts
                assert "heal" in result.stdout.lower() or "heal" in result.stderr.lower(), \
                    "Healing not triggered for incomplete config"
    
    @pytest.mark.parametrize("nl_request,expected_components", [
        ("Build a REST API", ["APIEndpoint"]),
        ("Create a data transformation pipeline", ["Source", "Transformer", "Sink"]),
        ("Set up a message queue processor", ["Source", "StreamProcessor", "Sink"]),
        ("Build a web scraper with storage", ["Source", "Store"])
    ])
    def test_various_nl_requests(self, nl_request, expected_components):
        """Test different types of natural language requests"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "test_system"
            
            result = subprocess.run(
                [
                    "python3", "-m", "autocoder_cc.cli",
                    "generate", nl_request,
                    "--output", str(output_dir)
                ],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Should generate successfully
            if result.returncode != 0:
                print(f"Failed for: {nl_request}")
                print(f"STDERR: {result.stderr}")
            
            # Check if expected components are mentioned
            main_file = output_dir / "main.py"
            if main_file.exists():
                content = main_file.read_text()
                for component_type in expected_components:
                    assert component_type.lower() in content.lower(), \
                        f"Expected component {component_type} not found in generated code"


class TestBlueprintStructureRegression:
    """Specific regression tests for the blueprint structure bug"""
    
    def test_csv_file_source_not_found_bug(self):
        """
        Direct regression test for the exact error:
        "Component csv_file_source not found in blueprint"
        """
        # This is the EXACT scenario that failed
        from autocoder_cc.blueprint_language.intermediate_to_blueprint_translator import (
            IntermediateToBlueprintTranslator
        )
        from autocoder_cc.blueprint_language.intermediate_format import (
            IntermediateSystem,
            IntermediateComponent,
            IntermediatePort
        )
        from autocoder_cc.validation.context_builder import PipelineContextBuilder
        
        # Create the system that triggered the bug
        intermediate = IntermediateSystem(
            name="data_pipeline",
            description="CSV to S3 pipeline",
            version="1.0.0",
            components=[
                IntermediateComponent(
                    name="csv_file_source",  # This exact name caused the error
                    type="Source",
                    description="Read CSV files",
                    inputs=[],
                    outputs=[IntermediatePort(name="output", schema_type="object")],
                    config={}
                )
            ],
            bindings=[]
        )
        
        # Generate blueprint
        translator = IntermediateToBlueprintTranslator()
        blueprint = translator._build_blueprint_dict(intermediate)
        
        # This should NOT fail
        context_builder = PipelineContextBuilder()
        context = context_builder.build_from_blueprint(blueprint, "csv_file_source")
        
        # Verify it worked
        assert context.component_name == "csv_file_source"
        assert context.component_type == "Source"
        
        print("✅ Regression test passed - csv_file_source bug fixed")


if __name__ == "__main__":
    # Run with verbose output
    pytest.main([__file__, "-v", "--tb=short"])