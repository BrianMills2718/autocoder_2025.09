#!/usr/bin/env python3
"""
Comprehensive Unit Tests for DocumentationHealthValidator
Tests all methods with edge cases, error conditions, and production scenarios
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from autocoder_cc.tools.ci.validate_doc_health import DocumentationHealthValidator


class TestDocumentationHealthValidator:
    """Comprehensive test suite for DocumentationHealthValidator"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.validator = DocumentationHealthValidator()
        self.test_data_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Cleanup after each test method"""
        import shutil
        shutil.rmtree(self.test_data_dir, ignore_errors=True)
    
    def create_test_report(self, health_score=95, high_issues=0, total_issues=5):
        """Create a test health report file"""
        report_data = {
            "health_score": health_score,
            "statistics": {
                "high_issues": high_issues,
                "total_issues": total_issues
            },
            "coverage": {
                "overall": 0.85,
                "documentation": 0.90
            }
        }
        report_path = os.path.join(self.test_data_dir, "test_report.json")
        with open(report_path, 'w') as f:
            json.dump(report_data, f)
        return report_path
    
    def test_init_default_values(self):
        """Test validator initialization with default values"""
        validator = DocumentationHealthValidator()
        assert validator.health_threshold == 90
        assert validator.high_issues_threshold == 0
    
    def test_init_custom_values(self):
        """Test validator initialization with custom threshold values"""
        validator = DocumentationHealthValidator(health_threshold=85, high_issues_threshold=2)
        assert validator.health_threshold == 85
        assert validator.high_issues_threshold == 2
    
    def test_init_none_values_use_defaults(self):
        """Test that None values fallback to defaults"""
        validator = DocumentationHealthValidator(health_threshold=None, high_issues_threshold=None)
        assert validator.health_threshold == 90
        assert validator.high_issues_threshold == 0
    
    def test_validate_health_report_success(self, capsys):
        """Test successful validation with passing health report"""
        report_path = self.create_test_report(health_score=95, high_issues=0)
        
        result = self.validator.validate_health_report(report_path)
        
        assert result is True
        captured = capsys.readouterr()
        assert "📊 Health score: 95" in captured.out
        assert "✅ Documentation health check passed" in captured.out
    
    def test_validate_health_report_low_score_failure(self, capsys):
        """Test validation failure due to low health score"""
        report_path = self.create_test_report(health_score=85, high_issues=0)
        
        result = self.validator.validate_health_report(report_path)
        
        assert result is False
        captured = capsys.readouterr()
        assert "::error ::Documentation health score 85 below threshold (90)" in captured.out
        assert "❌ Documentation health check failed" in captured.out
    
    def test_validate_health_report_high_issues_failure(self, capsys):
        """Test validation failure due to high priority issues"""
        report_path = self.create_test_report(health_score=95, high_issues=2)
        
        result = self.validator.validate_health_report(report_path)
        
        assert result is False
        captured = capsys.readouterr()
        assert "::error ::2 high priority documentation issues detected (max: 0)" in captured.out
        assert "❌ Documentation health check failed" in captured.out
    
    def test_validate_health_report_multiple_failures(self, capsys):
        """Test validation with multiple failure conditions"""
        report_path = self.create_test_report(health_score=75, high_issues=3)
        
        result = self.validator.validate_health_report(report_path)
        
        assert result is False
        captured = capsys.readouterr()
        assert "::error ::Documentation health score 75 below threshold (90)" in captured.out
        assert "::error ::3 high priority documentation issues detected (max: 0)" in captured.out
    
    def test_validate_health_report_file_not_found(self, capsys):
        """Test validation with non-existent file"""
        non_existent_path = "/path/that/does/not/exist.json"
        
        result = self.validator.validate_health_report(non_existent_path)
        
        assert result is False
        captured = capsys.readouterr()
        assert "::error ::Health report file not found:" in captured.out
    
    def test_validate_health_report_invalid_json(self, capsys):
        """Test validation with malformed JSON file"""
        invalid_json_path = os.path.join(self.test_data_dir, "invalid.json")
        with open(invalid_json_path, 'w') as f:
            f.write("{ invalid json content")
        
        result = self.validator.validate_health_report(invalid_json_path)
        
        assert result is False
        captured = capsys.readouterr()
        assert "::error ::Invalid JSON in health report:" in captured.out
    
    def test_validate_health_report_missing_health_score(self):
        """Test validation with missing health_score field"""
        report_data = {
            "statistics": {"high_issues": 0, "total_issues": 5},
            "coverage": {"overall": 0.85}
        }
        report_path = os.path.join(self.test_data_dir, "missing_score.json")
        with open(report_path, 'w') as f:
            json.dump(report_data, f)
        
        result = self.validator.validate_health_report(report_path)
        
        # Should default to 0 and fail validation
        assert result is False
    
    def test_validate_health_report_missing_statistics(self):
        """Test validation with missing statistics section"""
        report_data = {
            "health_score": 95,
            "coverage": {"overall": 0.85}
        }
        report_path = os.path.join(self.test_data_dir, "missing_stats.json")
        with open(report_path, 'w') as f:
            json.dump(report_data, f)
        
        result = self.validator.validate_health_report(report_path)
        
        # Should default high_issues to 0 and pass
        assert result is True
    
    def test_validate_health_report_boundary_conditions(self):
        """Test validation at exact threshold boundaries"""
        # Test exact threshold match
        report_path = self.create_test_report(health_score=90, high_issues=0)
        assert self.validator.validate_health_report(report_path) is True
        
        # Test one below threshold
        report_path = self.create_test_report(health_score=89, high_issues=0)
        assert self.validator.validate_health_report(report_path) is False
        
        # Test high issues at boundary
        validator_with_tolerance = DocumentationHealthValidator(high_issues_threshold=1)
        report_path = self.create_test_report(health_score=95, high_issues=1)
        assert validator_with_tolerance.validate_health_report(report_path) is True
        
        report_path = self.create_test_report(health_score=95, high_issues=2)
        assert validator_with_tolerance.validate_health_report(report_path) is False
    
    def test_get_health_summary_success(self):
        """Test successful health summary generation"""
        report_path = self.create_test_report(health_score=92, high_issues=1, total_issues=8)
        
        summary = self.validator.get_health_summary(report_path)
        
        assert summary['health_score'] == 92
        assert summary['high_issues'] == 1
        assert summary['total_issues'] == 8
        assert 'coverage' in summary
        assert 'validation_passed' in summary
        assert summary['validation_passed'] is False  # Due to high_issues > 0
    
    def test_get_health_summary_file_error(self):
        """Test health summary with file errors"""
        non_existent_path = "/path/that/does/not/exist.json"
        
        summary = self.validator.get_health_summary(non_existent_path)
        
        assert 'error' in summary
        assert 'No such file or directory' in summary['error'] or 'cannot find the path' in summary['error']
    
    def test_get_health_summary_malformed_json(self):
        """Test health summary with malformed JSON"""
        malformed_path = os.path.join(self.test_data_dir, "malformed.json")
        with open(malformed_path, 'w') as f:
            f.write("{ malformed json")
        
        summary = self.validator.get_health_summary(malformed_path)
        
        assert 'error' in summary
        assert 'Expecting' in summary['error'] or 'JSON' in summary['error']
    
    def test_validate_report_data_edge_cases(self):
        """Test _validate_report_data with edge cases"""
        # Test with extreme values
        extreme_data = {
            "health_score": 0,
            "statistics": {"high_issues": 999, "total_issues": 1000}
        }
        result = self.validator._validate_report_data(extreme_data)
        assert result is False
        
        # Test with perfect score
        perfect_data = {
            "health_score": 100,
            "statistics": {"high_issues": 0, "total_issues": 0}
        }
        result = self.validator._validate_report_data(perfect_data)
        assert result is True
    
    def test_validate_report_data_missing_nested_fields(self):
        """Test validation with missing nested fields in statistics"""
        data_missing_high_issues = {
            "health_score": 95,
            "statistics": {"total_issues": 5}
        }
        result = self.validator._validate_report_data(data_missing_high_issues)
        # Should default to 0 and pass
        assert result is True
    
    def test_custom_thresholds_validation(self):
        """Test validation with custom threshold values"""
        strict_validator = DocumentationHealthValidator(health_threshold=95, high_issues_threshold=0)
        lenient_validator = DocumentationHealthValidator(health_threshold=80, high_issues_threshold=5)
        
        report_path = self.create_test_report(health_score=85, high_issues=2)
        
        # Should fail strict validation
        assert strict_validator.validate_health_report(report_path) is False
        
        # Should pass lenient validation
        assert lenient_validator.validate_health_report(report_path) is True
    
    def test_github_actions_annotation_format(self, capsys):
        """Test that error messages use proper GitHub Actions annotation format"""
        report_path = self.create_test_report(health_score=75, high_issues=3)
        
        self.validator.validate_health_report(report_path)
        
        captured = capsys.readouterr()
        # Check for proper GitHub Actions annotation format
        assert "::error ::" in captured.out
        assert captured.out.count("::error ::") == 2  # Two error conditions
    
    def test_unicode_handling(self):
        """Test handling of unicode characters in file paths and content"""
        unicode_data = {
            "health_score": 90,
            "statistics": {"high_issues": 0, "total_issues": 1},
            "unicode_field": "测试数据 with émojis 🚀"
        }
        unicode_path = os.path.join(self.test_data_dir, "unicode_test.json")
        with open(unicode_path, 'w', encoding='utf-8') as f:
            json.dump(unicode_data, f, ensure_ascii=False)
        
        result = self.validator.validate_health_report(unicode_path)
        assert result is True
    
    def test_concurrent_access_safety(self):
        """Test that validator handles concurrent access safely"""
        import threading
        import time
        
        report_path = self.create_test_report()
        results = []
        
        def validate_concurrently():
            validator = DocumentationHealthValidator()
            result = validator.validate_health_report(report_path)
            results.append(result)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=validate_concurrently)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All results should be True (successful validation)
        assert all(results)
        assert len(results) == 5


class TestDocumentationHealthValidatorCLI:
    """Test the CLI interface of the validator"""
    
    def setup_method(self):
        self.test_data_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        import shutil
        shutil.rmtree(self.test_data_dir, ignore_errors=True)
    
    def create_test_report(self, health_score=95, high_issues=0):
        """Create a test health report file"""
        report_data = {
            "health_score": health_score,
            "statistics": {"high_issues": high_issues, "total_issues": 5}
        }
        report_path = os.path.join(self.test_data_dir, "cli_test_report.json")
        with open(report_path, 'w') as f:
            json.dump(report_data, f)
        return report_path
    
    def test_cli_successful_validation(self):
        """Test CLI with successful validation"""
        from autocoder_cc.tools.ci.validate_doc_health import main
        
        report_path = self.create_test_report(health_score=95, high_issues=0)
        
        # Mock sys.argv and sys.exit
        with patch('sys.argv', ['validate_doc_health.py', report_path]):
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_with(0)
    
    def test_cli_failed_validation(self):
        """Test CLI with failed validation"""
        from autocoder_cc.tools.ci.validate_doc_health import main
        
        report_path = self.create_test_report(health_score=75, high_issues=2)
        
        with patch('sys.argv', ['validate_doc_health.py', report_path]):
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_with(1)
    
    def test_cli_custom_thresholds(self):
        """Test CLI with custom threshold arguments"""
        from autocoder_cc.tools.ci.validate_doc_health import main
        
        report_path = self.create_test_report(health_score=85, high_issues=1)
        
        # Should fail with default thresholds
        with patch('sys.argv', ['validate_doc_health.py', report_path]):
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_with(1)
        
        # Should pass with lenient thresholds
        with patch('sys.argv', ['validate_doc_health.py', report_path, '--health-threshold', '80', '--max-high-issues', '2']):
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_with(0)
    
    def test_cli_summary_mode(self):
        """Test CLI summary mode"""
        from autocoder_cc.tools.ci.validate_doc_health import main
        
        report_path = self.create_test_report(health_score=88, high_issues=1)
        
        with patch('sys.argv', ['validate_doc_health.py', report_path, '--summary']):
            with patch('sys.exit') as mock_exit:
                with patch('builtins.print') as mock_print:
                    main()
                    mock_exit.assert_called_with(0)
                    # Should print JSON summary
                    printed_output = ' '.join([str(call) for call in mock_print.call_args_list])
                    assert '"health_score": 88' in printed_output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])