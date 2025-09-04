#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Health Thresholds Configuration
Tests YAML loading, validation, and industry standard compliance
"""

import pytest
import yaml
import tempfile
import os
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class ValidationResult:
    """Container for validation results"""
    
    def __init__(self, errors=None, warnings=None):
        self.errors = errors or []
        self.warnings = warnings or []
    
    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0
    
    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


class ConfigurationError(Exception):
    """Exception raised for configuration-related errors"""
    pass


class HealthThresholdsValidator:
    """Validator for health threshold configurations"""
    
    REQUIRED_FIELDS = {
        'health_score': {
            'type': dict,
            'required_subfields': ['minimum', 'justification']
        },
        'high_priority_issues': {
            'type': dict,
            'required_subfields': ['maximum', 'justification']
        }
    }
    
    JUSTIFICATION_REQUIRED_FIELDS = {
        'industry_standard': str,
        'citation': str,
        'benchmark_companies': list,
        'research_basis': str,
        'measurement_criteria': str
    }
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "autocoder_cc/tools/config/health_thresholds.yaml"
        self.config_data = None
    
    def load_configuration(self) -> dict:
        """Load and validate threshold configuration"""
        try:
            with open(self.config_path, 'r') as f:
                self.config_data = yaml.safe_load(f)
            return self.config_data
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration: {e}")
    
    def validate_structure(self) -> ValidationResult:
        """Validate configuration structure"""
        if not self.config_data:
            raise ValueError("Configuration not loaded. Call load_configuration() first.")
        
        errors = []
        warnings = []
        
        # Check required top-level fields
        for field_name, field_config in self.REQUIRED_FIELDS.items():
            if field_name not in self.config_data:
                errors.append(f"Missing required field: {field_name}")
                continue
            
            field_value = self.config_data[field_name]
            
            # Check field type
            if not isinstance(field_value, field_config['type']):
                errors.append(f"Field '{field_name}' must be of type {field_config['type'].__name__}")
                continue
            
            # Check required subfields
            for subfield in field_config['required_subfields']:
                if subfield not in field_value:
                    errors.append(f"Missing required subfield: {field_name}.{subfield}")
        
        return ValidationResult(errors=errors, warnings=warnings)
    
    def validate_justifications(self) -> ValidationResult:
        """Validate that justifications contain required industry research"""
        if not self.config_data:
            raise ValueError("Configuration not loaded. Call load_configuration() first.")
        
        errors = []
        warnings = []
        
        for threshold_name in ['health_score', 'high_priority_issues']:
            if threshold_name not in self.config_data:
                continue
            
            justification = self.config_data[threshold_name].get('justification', {})
            
            for required_field, expected_type in self.JUSTIFICATION_REQUIRED_FIELDS.items():
                if required_field not in justification:
                    errors.append(f"Missing justification field: {threshold_name}.justification.{required_field}")
                    continue
                
                value = justification[required_field]
                if not isinstance(value, expected_type):
                    errors.append(f"Justification field '{threshold_name}.justification.{required_field}' must be of type {expected_type.__name__}")
                    continue
                
                # Validate specific content requirements
                if required_field == 'citation' and not self._is_valid_url(value):
                    warnings.append(f"Citation URL appears invalid: {value}")
                
                if required_field == 'benchmark_companies' and len(value) < 3:
                    warnings.append(f"Benchmark companies list should contain at least 3 companies, found {len(value)}")
        
        return ValidationResult(errors=errors, warnings=warnings)
    
    def validate_threshold_values(self) -> ValidationResult:
        """Validate threshold values are within reasonable ranges"""
        if not self.config_data:
            raise ValueError("Configuration not loaded. Call load_configuration() first.")
        
        errors = []
        warnings = []
        
        # Validate health score threshold
        if 'health_score' in self.config_data:
            health_min = self.config_data['health_score'].get('minimum')
            if health_min is not None:
                if not isinstance(health_min, (int, float)):
                    errors.append("health_score.minimum must be a number")
                elif health_min < 0 or health_min > 100:
                    errors.append("health_score.minimum must be between 0 and 100")
                elif health_min < 70:
                    warnings.append(f"health_score.minimum of {health_min} is quite low for production systems")
                elif health_min > 98:
                    warnings.append(f"health_score.minimum of {health_min} may be unrealistically high")
        
        # Validate high priority issues threshold
        if 'high_priority_issues' in self.config_data:
            issues_max = self.config_data['high_priority_issues'].get('maximum')
            if issues_max is not None:
                if not isinstance(issues_max, int):
                    errors.append("high_priority_issues.maximum must be an integer")
                elif issues_max < 0:
                    errors.append("high_priority_issues.maximum cannot be negative")
                elif issues_max > 10:
                    warnings.append(f"high_priority_issues.maximum of {issues_max} may be too permissive")
        
        return ValidationResult(errors=errors, warnings=warnings)
    
    def _is_valid_url(self, url: str) -> bool:
        """Basic URL validation"""
        return url.startswith(('http://', 'https://')) and '.' in url


class TestHealthThresholdsValidator:
    """Comprehensive test suite for health threshold configuration validation"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.test_data_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        import shutil
        shutil.rmtree(self.test_data_dir, ignore_errors=True)
    
    def create_test_config(self, config_data):
        """Create a test configuration file"""
        config_path = os.path.join(self.test_data_dir, "test_thresholds.yaml")
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        return config_path
    
    def test_load_valid_configuration(self):
        """Test loading a valid configuration"""
        config_data = {
            'health_score': {
                'minimum': 90,
                'justification': {
                    'industry_standard': 'IEEE Standard 1063-2001',
                    'citation': 'https://standards.ieee.org/standard/1063-2001.html',
                    'benchmark_companies': ['Google', 'Microsoft', 'Amazon'],
                    'research_basis': 'Analysis of 50 enterprise companies',
                    'measurement_criteria': 'Based on completeness, accuracy, accessibility'
                }
            },
            'high_priority_issues': {
                'maximum': 0,
                'justification': {
                    'industry_standard': 'Zero-defect policies',
                    'citation': 'https://example.com/zero-defect-research',
                    'benchmark_companies': ['Netflix', 'Spotify', 'Stripe'],
                    'research_basis': 'Critical issues block 50% of developers',
                    'measurement_criteria': 'Impact on developer productivity'
                }
            }
        }
        
        config_path = self.create_test_config(config_data)
        validator = HealthThresholdsValidator(config_path)
        
        loaded_config = validator.load_configuration()
        assert loaded_config == config_data
    
    def test_load_nonexistent_file(self):
        """Test loading configuration from non-existent file"""
        validator = HealthThresholdsValidator("/path/that/does/not/exist.yaml")
        
        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            validator.load_configuration()
    
    def test_load_invalid_yaml(self):
        """Test loading malformed YAML configuration"""
        invalid_yaml_path = os.path.join(self.test_data_dir, "invalid.yaml")
        with open(invalid_yaml_path, 'w') as f:
            f.write("invalid: yaml: content: [unclosed")
        
        validator = HealthThresholdsValidator(invalid_yaml_path)
        
        with pytest.raises(ConfigurationError, match="Invalid YAML"):
            validator.load_configuration()
    
    def test_validate_structure_success(self):
        """Test successful structure validation"""
        config_data = {
            'health_score': {
                'minimum': 90,
                'justification': {'industry_standard': 'test'}
            },
            'high_priority_issues': {
                'maximum': 0,
                'justification': {'research_basis': 'test'}
            }
        }
        
        config_path = self.create_test_config(config_data)
        validator = HealthThresholdsValidator(config_path)
        validator.load_configuration()
        
        result = validator.validate_structure()
        assert result.is_valid
    
    def test_validate_structure_missing_top_level_fields(self):
        """Test structure validation with missing top-level fields"""
        config_data = {
            'health_score': {
                'minimum': 90,
                'justification': {}
            }
            # Missing 'high_priority_issues'
        }
        
        config_path = self.create_test_config(config_data)
        validator = HealthThresholdsValidator(config_path)
        validator.load_configuration()
        
        result = validator.validate_structure()
        assert not result.is_valid
        assert any("Missing required field: high_priority_issues" in error for error in result.errors)
    
    def test_validate_structure_wrong_field_type(self):
        """Test structure validation with wrong field types"""
        config_data = {
            'health_score': "should be dict not string",
            'high_priority_issues': {
                'maximum': 0,
                'justification': {}
            }
        }
        
        config_path = self.create_test_config(config_data)
        validator = HealthThresholdsValidator(config_path)
        validator.load_configuration()
        
        result = validator.validate_structure()
        assert not result.is_valid
        assert any("must be of type dict" in error for error in result.errors)
    
    def test_validate_structure_missing_subfields(self):
        """Test structure validation with missing required subfields"""
        config_data = {
            'health_score': {
                'minimum': 90
                # Missing 'justification'
            },
            'high_priority_issues': {
                # Missing 'maximum'
                'justification': {}
            }
        }
        
        config_path = self.create_test_config(config_data)
        validator = HealthThresholdsValidator(config_path)
        validator.load_configuration()
        
        result = validator.validate_structure()
        assert not result.is_valid
        assert any("Missing required subfield: health_score.justification" in error for error in result.errors)
        assert any("Missing required subfield: high_priority_issues.maximum" in error for error in result.errors)
    
    def test_validate_justifications_success(self):
        """Test successful justification validation"""
        config_data = {
            'health_score': {
                'minimum': 90,
                'justification': {
                    'industry_standard': 'IEEE Standard 1063-2001',
                    'citation': 'https://standards.ieee.org/standard/1063-2001.html',
                    'benchmark_companies': ['Google', 'Microsoft', 'Amazon'],
                    'research_basis': 'Analysis of 50 enterprise companies',
                    'measurement_criteria': 'Based on completeness, accuracy, accessibility'
                }
            },
            'high_priority_issues': {
                'maximum': 0,
                'justification': {
                    'industry_standard': 'Zero-defect policies',
                    'citation': 'https://example.com/research',
                    'benchmark_companies': ['Netflix', 'Spotify', 'Stripe'],
                    'research_basis': 'Critical issues impact',
                    'measurement_criteria': 'Developer productivity metrics'
                }
            }
        }
        
        config_path = self.create_test_config(config_data)
        validator = HealthThresholdsValidator(config_path)
        validator.load_configuration()
        
        result = validator.validate_justifications()
        assert result.is_valid
    
    def test_validate_justifications_missing_fields(self):
        """Test justification validation with missing required fields"""
        config_data = {
            'health_score': {
                'minimum': 90,
                'justification': {
                    'industry_standard': 'IEEE Standard 1063-2001',
                    # Missing other required fields
                }
            },
            'high_priority_issues': {
                'maximum': 0,
                'justification': {}  # Empty justification
            }
        }
        
        config_path = self.create_test_config(config_data)
        validator = HealthThresholdsValidator(config_path)
        validator.load_configuration()
        
        result = validator.validate_justifications()
        assert not result.is_valid
        assert len(result.errors) >= 8  # Multiple missing fields
    
    def test_validate_justifications_wrong_types(self):
        """Test justification validation with wrong field types"""
        config_data = {
            'health_score': {
                'minimum': 90,
                'justification': {
                    'industry_standard': 123,  # Should be string
                    'citation': 'https://example.com',
                    'benchmark_companies': 'not a list',  # Should be list
                    'research_basis': 'test',
                    'measurement_criteria': 'test'
                }
            },
            'high_priority_issues': {
                'maximum': 0,
                'justification': {
                    'industry_standard': 'test',
                    'citation': 'https://example.com',
                    'benchmark_companies': ['test'],
                    'research_basis': 'test',
                    'measurement_criteria': 'test'
                }
            }
        }
        
        config_path = self.create_test_config(config_data)
        validator = HealthThresholdsValidator(config_path)
        validator.load_configuration()
        
        result = validator.validate_justifications()
        assert not result.is_valid
        assert any("must be of type str" in error for error in result.errors)
        assert any("must be of type list" in error for error in result.errors)
    
    def test_validate_justifications_url_warnings(self):
        """Test justification validation generates warnings for invalid URLs"""
        config_data = {
            'health_score': {
                'minimum': 90,
                'justification': {
                    'industry_standard': 'test',
                    'citation': 'not-a-valid-url',
                    'benchmark_companies': ['Company1', 'Company2'],
                    'research_basis': 'test',
                    'measurement_criteria': 'test'
                }
            },
            'high_priority_issues': {
                'maximum': 0,
                'justification': {
                    'industry_standard': 'test',
                    'citation': 'https://valid.example.com',
                    'benchmark_companies': ['Company1'],  # Too few companies
                    'research_basis': 'test',
                    'measurement_criteria': 'test'
                }
            }
        }
        
        config_path = self.create_test_config(config_data)
        validator = HealthThresholdsValidator(config_path)
        validator.load_configuration()
        
        result = validator.validate_justifications()
        assert result.is_valid  # No errors, but should have warnings
        assert result.has_warnings
        assert any("Citation URL appears invalid" in warning for warning in result.warnings)
        assert any("should contain at least 3 companies" in warning for warning in result.warnings)
    
    def test_validate_threshold_values_success(self):
        """Test successful threshold value validation"""
        config_data = {
            'health_score': {
                'minimum': 90,
                'justification': {}
            },
            'high_priority_issues': {
                'maximum': 0,
                'justification': {}
            }
        }
        
        config_path = self.create_test_config(config_data)
        validator = HealthThresholdsValidator(config_path)
        validator.load_configuration()
        
        result = validator.validate_threshold_values()
        assert result.is_valid
    
    def test_validate_threshold_values_out_of_range(self):
        """Test threshold value validation with out-of-range values"""
        config_data = {
            'health_score': {
                'minimum': 150,  # Invalid: > 100
                'justification': {}
            },
            'high_priority_issues': {
                'maximum': -5,  # Invalid: negative
                'justification': {}
            }
        }
        
        config_path = self.create_test_config(config_data)
        validator = HealthThresholdsValidator(config_path)
        validator.load_configuration()
        
        result = validator.validate_threshold_values()
        assert not result.is_valid
        assert any("must be between 0 and 100" in error for error in result.errors)
        assert any("cannot be negative" in error for error in result.errors)
    
    def test_validate_threshold_values_wrong_types(self):
        """Test threshold value validation with wrong types"""
        config_data = {
            'health_score': {
                'minimum': "ninety",  # Should be number
                'justification': {}
            },
            'high_priority_issues': {
                'maximum': 2.5,  # Should be integer
                'justification': {}
            }
        }
        
        config_path = self.create_test_config(config_data)
        validator = HealthThresholdsValidator(config_path)
        validator.load_configuration()
        
        result = validator.validate_threshold_values()
        assert not result.is_valid
        assert any("must be a number" in error for error in result.errors)
        assert any("must be an integer" in error for error in result.errors)
    
    def test_validate_threshold_values_warnings(self):
        """Test threshold value validation generates appropriate warnings"""
        config_data = {
            'health_score': {
                'minimum': 50,  # Too low
                'justification': {}
            },
            'high_priority_issues': {
                'maximum': 15,  # Too permissive
                'justification': {}
            }
        }
        
        config_path = self.create_test_config(config_data)
        validator = HealthThresholdsValidator(config_path)
        validator.load_configuration()
        
        result = validator.validate_threshold_values()
        assert result.is_valid  # No errors, but should have warnings
        assert result.has_warnings
        assert any("quite low for production systems" in warning for warning in result.warnings)
        assert any("may be too permissive" in warning for warning in result.warnings)
    
    def test_validate_without_loading_config_raises_error(self):
        """Test that validation methods require configuration to be loaded first"""
        validator = HealthThresholdsValidator()
        
        with pytest.raises(ValueError, match="Configuration not loaded"):
            validator.validate_structure()
        
        with pytest.raises(ValueError, match="Configuration not loaded"):
            validator.validate_justifications()
        
        with pytest.raises(ValueError, match="Configuration not loaded"):
            validator.validate_threshold_values()
    
    def test_edge_case_empty_configuration(self):
        """Test validation with empty configuration"""
        config_data = {}
        
        config_path = self.create_test_config(config_data)
        validator = HealthThresholdsValidator(config_path)
        validator.load_configuration()
        
        structure_result = validator.validate_structure()
        assert not structure_result.is_valid
        assert len(structure_result.errors) >= 2  # Missing both required fields
    
    def test_edge_case_null_values(self):
        """Test validation with null/None values"""
        config_data = {
            'health_score': {
                'minimum': None,
                'justification': None
            },
            'high_priority_issues': {
                'maximum': None,
                'justification': None
            }
        }
        
        config_path = self.create_test_config(config_data)
        validator = HealthThresholdsValidator(config_path)
        validator.load_configuration()
        
        # Structure validation should pass (fields exist)
        structure_result = validator.validate_structure()
        # But other validations should catch the None values
        threshold_result = validator.validate_threshold_values()
        # Should handle None values gracefully


if __name__ == "__main__":
    pytest.main([__file__, "-v"])