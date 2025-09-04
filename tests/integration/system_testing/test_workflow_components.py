#!/usr/bin/env python3
"""
Integration Tests for Workflow Components
Tests actual script execution in workflow context with real repo states
"""

import pytest
import subprocess
import tempfile
import json
import os
import yaml
from pathlib import Path
import sys
import shutil
from unittest.mock import patch

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestWorkflowComponentsIntegration:
    """Integration tests for workflow script execution"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.test_repo_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
        # Create a mock repository structure
        self.create_mock_repo_structure()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_repo_dir, ignore_errors=True)
    
    def create_mock_repo_structure(self):
        """Create a realistic repository structure for testing"""
        # Create basic directory structure
        dirs = [
            "docs",
            "autocoder_cc/tools/documentation", 
            "autocoder_cc/tools/config",
            "autocoder_cc/tools/scripts",
            "autocoder_cc/tools/ci",
            ".github/workflows"
        ]
        
        for dir_path in dirs:
            os.makedirs(os.path.join(self.test_repo_dir, dir_path), exist_ok=True)
        
        # Create sample documentation files
        self.create_sample_docs()
        
        # Create configuration files
        self.create_config_files()
        
        # Create workflow scripts (copy from actual project)
        self.setup_workflow_scripts()
    
    def create_sample_docs(self):
        """Create sample documentation files for testing"""
        docs_dir = os.path.join(self.test_repo_dir, "docs")
        
        # Create README.md
        readme_content = """# Test Project
        
This is a test project for documentation health validation.

## Features
- Feature 1: Complete implementation
- Feature 2: Partial implementation
- Feature 3: TODO

## Installation
Run `pip install -r requirements.txt`

## Usage
Example usage here.
"""
        with open(os.path.join(docs_dir, "README.md"), 'w') as f:
            f.write(readme_content)
        
        # Create API documentation
        api_doc_content = """# API Documentation

## Endpoints

### GET /api/health
Returns health status

### POST /api/data
Creates new data entry

## Authentication
Use API key in header
"""
        with open(os.path.join(docs_dir, "api.md"), 'w') as f:
            f.write(api_doc_content)
        
        # Create incomplete documentation
        incomplete_content = """# Incomplete Documentation

TODO: Add proper documentation
"""
        with open(os.path.join(docs_dir, "incomplete.md"), 'w') as f:
            f.write(incomplete_content)
    
    def create_config_files(self):
        """Create configuration files for testing"""
        config_dir = os.path.join(self.test_repo_dir, "autocoder_cc/tools/config")
        
        # Create doc_guard.yaml
        doc_guard_config = {
            "include_patterns": [
                "**/*.md",
                "**/*.rst"
            ],
            "exclude_patterns": [
                "**/node_modules/**",
                "**/.*/**"
            ],
            "health_checks": {
                "completeness": {"weight": 0.4},
                "accuracy": {"weight": 0.3},
                "accessibility": {"weight": 0.3}
            }
        }
        
        with open(os.path.join(config_dir, "doc_guard.yaml"), 'w') as f:
            yaml.dump(doc_guard_config, f)
        
        # Create health_thresholds.yaml
        health_thresholds = {
            "health_score": {
                "minimum": 90,
                "justification": {
                    "industry_standard": "IEEE Standard 1063-2001 requires 90%+ documentation completeness",
                    "citation": "https://standards.ieee.org/standard/1063-2001.html",
                    "benchmark_companies": ["Google", "Microsoft", "Amazon"],
                    "research_basis": "Analysis of 50 enterprise companies shows 90% threshold optimal",
                    "measurement_criteria": "Based on completeness, accuracy, accessibility, maintainability"
                }
            },
            "high_priority_issues": {
                "maximum": 0,
                "justification": {
                    "industry_standard": "Zero-defect policies at Netflix, Spotify, Stripe",
                    "citation": "https://example.com/zero-defect-research",
                    "benchmark_companies": ["Netflix", "Spotify", "Stripe"],
                    "research_basis": "Critical doc issues cost 40hrs developer time each",
                    "measurement_criteria": "Impact on developer productivity"
                }
            }
        }
        
        with open(os.path.join(config_dir, "health_thresholds.yaml"), 'w') as f:
            yaml.dump(health_thresholds, f)
    
    def setup_workflow_scripts(self):
        """Setup workflow scripts by copying from project"""
        scripts_source_dir = project_root / "autocoder_cc" / "tools"
        scripts_target_dir = Path(self.test_repo_dir) / "autocoder_cc" / "tools"
        
        # Copy essential scripts
        essential_scripts = [
            "documentation/enhanced_doc_health_dashboard.py",
            "scripts/roadmap_lint.py", 
            "ci/validate_doc_health.py"
        ]
        
        for script_path in essential_scripts:
            source_file = scripts_source_dir / script_path
            target_file = scripts_target_dir / script_path
            
            if source_file.exists():
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, target_file)
    
    def test_enhanced_doc_health_dashboard_execution(self):
        """Test enhanced_doc_health_dashboard.py with various repo states"""
        os.chdir(self.test_repo_dir)
        
        script_path = os.path.join(self.test_repo_dir, 
                                 "autocoder_cc/tools/documentation/enhanced_doc_health_dashboard.py")
        
        if not os.path.exists(script_path):
            pytest.skip("enhanced_doc_health_dashboard.py not available")
        
        # Test basic execution
        result = subprocess.run([
            sys.executable, script_path,
            "--repo-root", ".",
            "--config", "autocoder_cc/tools/config/doc_guard.yaml"
        ], capture_output=True, text=True, timeout=30)
        
        # Should complete without errors
        assert result.returncode == 0, f"Script failed with stderr: {result.stderr}"
        
        # Should generate output
        assert len(result.stdout) > 0, "Script produced no output"
        
        # Check for expected output patterns
        output_lines = result.stdout.lower()
        expected_patterns = ["health", "score", "documentation"]
        for pattern in expected_patterns:
            assert pattern in output_lines, f"Expected pattern '{pattern}' not found in output"
    
    def test_enhanced_doc_health_dashboard_with_output_file(self):
        """Test enhanced_doc_health_dashboard.py with output file generation"""
        os.chdir(self.test_repo_dir)
        
        script_path = os.path.join(self.test_repo_dir,
                                 "autocoder_cc/tools/documentation/enhanced_doc_health_dashboard.py")
        
        if not os.path.exists(script_path):
            pytest.skip("enhanced_doc_health_dashboard.py not available")
        
        output_file = os.path.join(self.test_repo_dir, "health_report.json")
        
        # Execute with output file
        result = subprocess.run([
            sys.executable, script_path,
            "--repo-root", ".",
            "--config", "autocoder_cc/tools/config/doc_guard.yaml",
            "--output", output_file
        ], capture_output=True, text=True, timeout=30)
        
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert os.path.exists(output_file), "Output file was not created"
        
        # Validate output file content
        with open(output_file, 'r') as f:
            health_data = json.load(f)
        
        # Check required fields
        required_fields = ["health_score", "statistics", "timestamp"]
        for field in required_fields:
            assert field in health_data, f"Required field '{field}' missing from output"
        
        # Validate health score is a number
        health_score = health_data.get("health_score")
        assert isinstance(health_score, (int, float)), "Health score must be numeric"
        assert 0 <= health_score <= 100, "Health score must be between 0 and 100"
    
    def test_roadmap_lint_execution(self):
        """Test roadmap_lint.py with different roadmap conditions"""
        os.chdir(self.test_repo_dir)
        
        # Create a test roadmap file
        roadmap_content = """# Project Roadmap

## Phase 1: Foundation
- [x] Basic setup
- [x] Core architecture
- [ ] Initial testing

## Phase 2: Development  
- [ ] Feature implementation
- [ ] Integration testing
- [ ] Performance optimization

## Phase 3: Release
- [ ] Documentation completion
- [ ] Final testing
- [ ] Deployment
"""
        
        roadmap_path = os.path.join(self.test_repo_dir, "ROADMAP.md")
        with open(roadmap_path, 'w') as f:
            f.write(roadmap_content)
        
        script_path = os.path.join(self.test_repo_dir,
                                 "autocoder_cc/tools/scripts/roadmap_lint.py")
        
        if not os.path.exists(script_path):
            pytest.skip("roadmap_lint.py not available")
        
        # Test roadmap linting
        result = subprocess.run([
            sys.executable, script_path,
            roadmap_path
        ], capture_output=True, text=True, timeout=30)
        
        # Should complete successfully
        assert result.returncode == 0, f"Roadmap linting failed: {result.stderr}"
        
        # Should provide analysis output
        assert len(result.stdout) > 0, "Roadmap linting produced no output"
    
    def test_validate_doc_health_with_real_data(self):
        """Test validate_doc_health.py with real health report data"""
        os.chdir(self.test_repo_dir)
        
        # First generate a health report
        dashboard_script = os.path.join(self.test_repo_dir,
                                      "autocoder_cc/tools/documentation/enhanced_doc_health_dashboard.py")
        
        if not os.path.exists(dashboard_script):
            pytest.skip("enhanced_doc_health_dashboard.py not available")
        
        health_report_path = os.path.join(self.test_repo_dir, "test_health_report.json")
        
        # Generate health report
        result = subprocess.run([
            sys.executable, dashboard_script,
            "--repo-root", ".",
            "--config", "autocoder_cc/tools/config/doc_guard.yaml",
            "--output", health_report_path
        ], capture_output=True, text=True, timeout=30)
        
        assert result.returncode == 0, "Failed to generate health report"
        assert os.path.exists(health_report_path), "Health report not created"
        
        # Now test validation
        validate_script = os.path.join(self.test_repo_dir,
                                     "autocoder_cc/tools/ci/validate_doc_health.py")
        
        if not os.path.exists(validate_script):
            pytest.skip("validate_doc_health.py not available")
        
        validation_result = subprocess.run([
            sys.executable, validate_script,
            health_report_path,
            "--health-threshold", "50",  # Lower threshold for test data
            "--max-high-issues", "10"    # Allow some issues for test
        ], capture_output=True, text=True, timeout=30)
        
        # Validation should complete (may pass or fail depending on test data quality)
        assert validation_result.returncode in [0, 1], "Validation script should exit with 0 or 1"
        
        # Should produce structured output
        output = validation_result.stdout
        assert "Health score:" in output, "Should report health score"
        assert "High priority issues:" in output, "Should report high priority issues"
    
    def test_script_chaining_and_data_flow(self):
        """Test complete script chaining from health generation to validation"""
        os.chdir(self.test_repo_dir)
        
        # Step 1: Generate health dashboard
        dashboard_script = os.path.join(self.test_repo_dir,
                                      "autocoder_cc/tools/documentation/enhanced_doc_health_dashboard.py")
        
        if not os.path.exists(dashboard_script):
            pytest.skip("Scripts not available for chaining test")
        
        health_output = os.path.join(self.test_repo_dir, "chain_test_health.json")
        
        step1_result = subprocess.run([
            sys.executable, dashboard_script,
            "--repo-root", ".",
            "--config", "autocoder_cc/tools/config/doc_guard.yaml", 
            "--output", health_output
        ], capture_output=True, text=True, timeout=30)
        
        assert step1_result.returncode == 0, f"Step 1 failed: {step1_result.stderr}"
        assert os.path.exists(health_output), "Health report not generated"
        
        # Step 2: Validate generated health report
        validate_script = os.path.join(self.test_repo_dir,
                                     "autocoder_cc/tools/ci/validate_doc_health.py")
        
        if not os.path.exists(validate_script):
            pytest.skip("validate_doc_health.py not available for chaining")
        
        step2_result = subprocess.run([
            sys.executable, validate_script,
            health_output,
            "--summary"  # Use summary mode for structured output
        ], capture_output=True, text=True, timeout=30)
        
        assert step2_result.returncode == 0, f"Step 2 failed: {step2_result.stderr}"
        
        # Parse summary output
        try:
            summary_data = json.loads(step2_result.stdout)
            assert "health_score" in summary_data, "Summary missing health_score"
            assert "validation_passed" in summary_data, "Summary missing validation_passed"
        except json.JSONDecodeError:
            pytest.fail(f"Step 2 output is not valid JSON: {step2_result.stdout}")
    
    def test_error_handling_in_workflow_context(self):
        """Test error handling scenarios in workflow execution context"""
        os.chdir(self.test_repo_dir)
        
        # Test with missing configuration file
        dashboard_script = os.path.join(self.test_repo_dir,
                                      "autocoder_cc/tools/documentation/enhanced_doc_health_dashboard.py")
        
        if not os.path.exists(dashboard_script):
            pytest.skip("enhanced_doc_health_dashboard.py not available")
        
        # Test with non-existent config
        result = subprocess.run([
            sys.executable, dashboard_script,
            "--repo-root", ".",
            "--config", "nonexistent_config.yaml"
        ], capture_output=True, text=True, timeout=30)
        
        # Should fail gracefully
        assert result.returncode != 0, "Should fail with missing config"
        assert len(result.stderr) > 0, "Should provide error information"
        
        # Test validation with missing health report
        validate_script = os.path.join(self.test_repo_dir,
                                     "autocoder_cc/tools/ci/validate_doc_health.py")
        
        if os.path.exists(validate_script):
            validation_result = subprocess.run([
                sys.executable, validate_script,
                "nonexistent_report.json"
            ], capture_output=True, text=True, timeout=30)
            
            assert validation_result.returncode != 0, "Should fail with missing report"
            assert "::error ::" in validation_result.stdout, "Should use GitHub Actions error format"
    
    def test_script_execution_with_different_repo_states(self):
        """Test script execution with various repository states"""
        os.chdir(self.test_repo_dir)
        
        # Test with empty repository
        empty_repo_dir = os.path.join(self.test_repo_dir, "empty_repo")
        os.makedirs(empty_repo_dir)
        
        dashboard_script = os.path.join(self.test_repo_dir,
                                      "autocoder_cc/tools/documentation/enhanced_doc_health_dashboard.py")
        
        if not os.path.exists(dashboard_script):
            pytest.skip("enhanced_doc_health_dashboard.py not available")
        
        # Create minimal config for empty repo test
        empty_config = {"include_patterns": ["**/*.md"], "exclude_patterns": []}
        empty_config_path = os.path.join(empty_repo_dir, "config.yaml")
        with open(empty_config_path, 'w') as f:
            yaml.dump(empty_config, f)
        
        result = subprocess.run([
            sys.executable, dashboard_script,
            "--repo-root", empty_repo_dir,
            "--config", empty_config_path
        ], capture_output=True, text=True, timeout=30)
        
        # Should handle empty repository gracefully
        assert result.returncode == 0, f"Failed with empty repo: {result.stderr}"
        
        # Test with repository containing only binary files
        binary_repo_dir = os.path.join(self.test_repo_dir, "binary_repo")
        os.makedirs(binary_repo_dir)
        
        # Create a binary file
        binary_file = os.path.join(binary_repo_dir, "test.bin")
        with open(binary_file, 'wb') as f:
            f.write(b'\x00\x01\x02\x03\x04\x05')
        
        binary_config_path = os.path.join(binary_repo_dir, "config.yaml")
        with open(binary_config_path, 'w') as f:
            yaml.dump(empty_config, f)
        
        result = subprocess.run([
            sys.executable, dashboard_script,
            "--repo-root", binary_repo_dir,
            "--config", binary_config_path
        ], capture_output=True, text=True, timeout=30)
        
        # Should handle binary files gracefully
        assert result.returncode == 0, f"Failed with binary files: {result.stderr}"
    
    def test_performance_under_load(self):
        """Test script performance with larger repository structures"""
        os.chdir(self.test_repo_dir)
        
        # Create a larger documentation structure
        large_docs_dir = os.path.join(self.test_repo_dir, "large_docs")
        os.makedirs(large_docs_dir, exist_ok=True)
        
        # Generate multiple documentation files
        for i in range(50):  # Create 50 documentation files
            doc_content = f"""# Documentation File {i}
            
This is documentation file number {i}.

## Section 1
Content for section 1 of file {i}.

## Section 2
Content for section 2 of file {i}.

### Subsection 2.1
More detailed content here.

## Conclusion
Final thoughts for file {i}.
"""
            doc_path = os.path.join(large_docs_dir, f"doc_{i:03d}.md")
            with open(doc_path, 'w') as f:
                f.write(doc_content)
        
        dashboard_script = os.path.join(self.test_repo_dir,
                                      "autocoder_cc/tools/documentation/enhanced_doc_health_dashboard.py")
        
        if not os.path.exists(dashboard_script):
            pytest.skip("enhanced_doc_health_dashboard.py not available")
        
        # Measure execution time
        import time
        start_time = time.time()
        
        result = subprocess.run([
            sys.executable, dashboard_script,
            "--repo-root", ".",
            "--config", "autocoder_cc/tools/config/doc_guard.yaml"
        ], capture_output=True, text=True, timeout=120)  # Longer timeout for large repo
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert result.returncode == 0, f"Failed with large repository: {result.stderr}"
        assert execution_time < 60, f"Execution took too long: {execution_time:.2f}s"
        
        # Verify output quality
        assert len(result.stdout) > 0, "No output generated for large repository"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])