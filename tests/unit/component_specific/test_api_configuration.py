import pytest
import os
from unittest.mock import patch
from autocoder_cc.core.config import Settings

class TestAPIConfiguration:
    """Test suite for API configuration validation and integration"""
    
    def test_github_token_validation_success(self):
        """Test GitHub token validation with valid token"""
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'ghp_1234567890123456789012345678901234567890EXTRA'}, clear=True):
            settings = Settings()
            token = settings.get_github_token()
            assert token == 'ghp_1234567890123456789012345678901234567890EXTRA'
    
    def test_github_token_validation_failure_missing(self):
        """Test GitHub token validation fails when missing"""
        # Clear environment and create settings with no token
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            # Manually set the field to None to simulate missing token
            settings.GITHUB_TOKEN = None
            with pytest.raises(ValueError, match="GITHUB_TOKEN is required"):
                settings.get_github_token()
    
    def test_github_token_validation_failure_format(self):
        """Test GitHub token validation fails with invalid format"""
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'invalid_token'}):
            settings = Settings()
            with pytest.raises(ValueError, match="Invalid GitHub token format"):
                settings.get_github_token()
    
    def test_aws_credentials_validation_success(self):
        """Test AWS credentials validation with valid credentials"""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'AKIA1234567890123456',
            'AWS_SECRET_ACCESS_KEY': '1234567890123456789012345678901234567890'
        }):
            settings = Settings()
            access_key, secret_key = settings.get_aws_credentials()
            assert access_key == 'AKIA1234567890123456'
            assert secret_key == '1234567890123456789012345678901234567890'
    
    def test_aws_credentials_validation_failure_missing(self):
        """Test AWS credentials validation fails when missing"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            with pytest.raises(ValueError, match="AWS credentials not configured"):
                settings.get_aws_credentials()
    
    def test_aws_credentials_has_credentials_check(self):
        """Test AWS has_credentials check works correctly"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert not settings.has_aws_credentials()
        
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'AKIA1234567890123456',
            'AWS_SECRET_ACCESS_KEY': '1234567890123456789012345678901234567890'
        }):
            settings = Settings()
            assert settings.has_aws_credentials()
    
    def test_datadog_credentials_validation_success(self):
        """Test Datadog credentials validation with valid credentials"""
        with patch.dict(os.environ, {
            'DATADOG_API_KEY': '12345678901234567890123456789012',
            'DATADOG_APP_KEY': '1234567890123456789012345678901234567890'
        }):
            settings = Settings()
            api_key, app_key = settings.get_datadog_credentials()
            assert api_key == '12345678901234567890123456789012'
            assert app_key == '1234567890123456789012345678901234567890'
    
    def test_datadog_credentials_validation_failure_missing(self):
        """Test Datadog credentials validation fails when missing"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            with pytest.raises(ValueError, match="Datadog credentials not configured"):
                settings.get_datadog_credentials()
    
    def test_datadog_credentials_has_credentials_check(self):
        """Test Datadog has_credentials check works correctly"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert not settings.has_datadog_credentials()
        
        with patch.dict(os.environ, {
            'DATADOG_API_KEY': '12345678901234567890123456789012',
            'DATADOG_APP_KEY': '1234567890123456789012345678901234567890'
        }):
            settings = Settings()
            assert settings.has_datadog_credentials()
    
    def test_prometheus_url_validation_success(self):
        """Test Prometheus URL validation with valid URLs"""
        with patch.dict(os.environ, {'PROMETHEUS_URL': 'http://localhost:9090'}):
            settings = Settings()
            url = settings.get_prometheus_url()
            assert url == 'http://localhost:9090'
        
        with patch.dict(os.environ, {'PROMETHEUS_URL': 'https://prometheus.example.com'}):
            settings = Settings()
            url = settings.get_prometheus_url()
            assert url == 'https://prometheus.example.com'
    
    def test_prometheus_url_validation_failure_invalid_format(self):
        """Test Prometheus URL validation fails with invalid format"""
        with patch.dict(os.environ, {'PROMETHEUS_URL': 'invalid-url'}):
            settings = Settings()
            with pytest.raises(ValueError, match="Invalid Prometheus URL format"):
                settings.get_prometheus_url()
    
    def test_all_api_keys_loaded_from_env(self):
        """Test that all API keys can be loaded from environment"""
        env_vars = {
            'GITHUB_TOKEN': 'ghp_1234567890123456789012345678901234567890EXTRA',
            'AWS_ACCESS_KEY_ID': 'AKIA1234567890123456',
            'AWS_SECRET_ACCESS_KEY': '1234567890123456789012345678901234567890',
            'DATADOG_API_KEY': '12345678901234567890123456789012',
            'DATADOG_APP_KEY': '1234567890123456789012345678901234567890',
            'PROMETHEUS_URL': 'http://localhost:9090'
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            # Verify all API credentials work
            assert settings.get_github_token()
            assert settings.get_aws_credentials()
            assert settings.get_datadog_credentials()
            assert settings.get_prometheus_url()
            
            # Verify availability checks
            assert settings.has_aws_credentials()
            assert settings.has_datadog_credentials()
    
    def test_config_fields_exist(self):
        """Test that all required API fields exist in Settings class"""
        settings = Settings()
        
        # Verify all new fields exist
        assert hasattr(settings, 'GITHUB_TOKEN'), "GITHUB_TOKEN field missing from Settings"
        assert hasattr(settings, 'AWS_ACCESS_KEY_ID'), "AWS_ACCESS_KEY_ID field missing from Settings"
        assert hasattr(settings, 'AWS_SECRET_ACCESS_KEY'), "AWS_SECRET_ACCESS_KEY field missing from Settings"
        assert hasattr(settings, 'DATADOG_API_KEY'), "DATADOG_API_KEY field missing from Settings"
        assert hasattr(settings, 'DATADOG_APP_KEY'), "DATADOG_APP_KEY field missing from Settings"
        assert hasattr(settings, 'PROMETHEUS_URL'), "PROMETHEUS_URL field missing from Settings"
        
        # Verify all methods exist
        assert hasattr(settings, 'get_github_token'), "get_github_token method missing"
        assert hasattr(settings, 'get_aws_credentials'), "get_aws_credentials method missing"
        assert hasattr(settings, 'has_aws_credentials'), "has_aws_credentials method missing"
        assert hasattr(settings, 'get_datadog_credentials'), "get_datadog_credentials method missing"
        assert hasattr(settings, 'has_datadog_credentials'), "has_datadog_credentials method missing"
        assert hasattr(settings, 'get_prometheus_url'), "get_prometheus_url method missing"

    def test_github_token_validation_failure_wrong_length(self):
        """Test GitHub token validation fails with wrong length token"""
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'ghp_short'}):
            settings = Settings()
            with pytest.raises(ValueError, match="Invalid GitHub token format"):
                settings.get_github_token()

    def test_aws_access_key_validation_failure_wrong_prefix(self):
        """Test AWS access key validation fails with wrong prefix"""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'INVALID1234567890123456',
            'AWS_SECRET_ACCESS_KEY': '1234567890123456789012345678901234567890'
        }):
            settings = Settings()
            with pytest.raises(ValueError, match="Invalid AWS Access Key ID format"):
                settings.get_aws_credentials()

    def test_aws_secret_key_validation_failure_wrong_length(self):
        """Test AWS secret key validation fails with wrong length"""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'AKIA1234567890123456',
            'AWS_SECRET_ACCESS_KEY': 'tooshort'
        }):
            settings = Settings()
            with pytest.raises(ValueError, match="Invalid AWS Secret Access Key format"):
                settings.get_aws_credentials()

    def test_datadog_api_key_validation_failure_wrong_length(self):
        """Test Datadog API key validation fails with wrong length"""
        with patch.dict(os.environ, {
            'DATADOG_API_KEY': 'tooshort',
            'DATADOG_APP_KEY': '1234567890123456789012345678901234567890'
        }):
            settings = Settings()
            with pytest.raises(ValueError, match="Invalid Datadog API key format"):
                settings.get_datadog_credentials()

    def test_datadog_app_key_validation_failure_wrong_length(self):
        """Test Datadog App key validation fails with wrong length"""
        with patch.dict(os.environ, {
            'DATADOG_API_KEY': '12345678901234567890123456789012',
            'DATADOG_APP_KEY': 'tooshort'
        }):
            settings = Settings()
            with pytest.raises(ValueError, match="Invalid Datadog Application key format"):
                settings.get_datadog_credentials()

    def test_datadog_api_key_validation_failure_non_hex(self):
        """Test Datadog API key validation fails with non-hex characters"""
        with patch.dict(os.environ, {
            'DATADOG_API_KEY': 'gggggggggggggggggggggggggggggggg',  # 32 chars but not hex
            'DATADOG_APP_KEY': '1234567890123456789012345678901234567890'
        }):
            settings = Settings()
            with pytest.raises(ValueError, match="Invalid Datadog API key format"):
                settings.get_datadog_credentials()

    def test_prometheus_url_default_value(self):
        """Test Prometheus URL uses default value when not set in environment"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            url = settings.get_prometheus_url()
            assert url == 'http://localhost:9090'