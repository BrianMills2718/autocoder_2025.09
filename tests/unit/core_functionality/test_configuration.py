#!/usr/bin/env python3
"""
Test Configuration - Verify config system works in dev/prod modes
Part of the CLAUDE.md critical fixes verification
"""
import pytest
import sys
import os

# Add project to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestConfiguration:
    """Verify configuration system works correctly"""
    
    def test_development_mode_config(self):
        """Test configuration loads with development defaults"""
        # Force development mode
        os.environ['ENVIRONMENT'] = 'development'
        
        # Import fresh
        import importlib
        if 'autocoder_cc.core.config' in sys.modules:
            del sys.modules['autocoder_cc.core.config']
        
        from autocoder_cc.core.config import Settings
        settings = Settings()
        
        assert settings.ENVIRONMENT == 'development'
        assert settings.JWT_SECRET_KEY == 'dev-jwt-secret-key-change-in-production'
        assert settings.KAFKA_BROKERS == 'localhost:9092'
        assert settings.DEBUG_MODE == True
        
    def test_jwt_secret_key_fallback(self):
        """Test JWT secret key provides development fallback"""
        from autocoder_cc.core.config import Settings
        
        # Clear any existing JWT_SECRET_KEY
        if 'JWT_SECRET_KEY' in os.environ:
            del os.environ['JWT_SECRET_KEY']
            
        settings = Settings(ENVIRONMENT='development')
        assert settings.JWT_SECRET_KEY == 'dev-jwt-secret-key-change-in-production'
        
    def test_kafka_brokers_fallback(self):
        """Test Kafka brokers provides development fallback"""
        from autocoder_cc.core.config import Settings
        
        # Clear any existing KAFKA_BROKERS
        if 'KAFKA_BROKERS' in os.environ:
            del os.environ['KAFKA_BROKERS']
            
        settings = Settings(ENVIRONMENT='development')
        assert settings.KAFKA_BROKERS == 'localhost:9092'
        
    def test_production_mode_validation(self):
        """Test production mode requires proper configuration"""
        from autocoder_cc.core.config import Settings
        
        # Test JWT_SECRET_KEY validation in production
        with pytest.raises(ValueError, match="JWT_SECRET_KEY environment variable is required"):
            settings = Settings(ENVIRONMENT='production', DEFAULT_JWT_SECRET_KEY=None)
            _ = settings.JWT_SECRET_KEY
            
    def test_infrastructure_ports(self):
        """Test infrastructure port configuration"""
        from autocoder_cc.core.config import Settings
        
        settings = Settings(ENVIRONMENT='development')
        assert settings.REDIS_PORT == 6379
        assert settings.POSTGRES_PORT == 5432
        assert settings.KAFKA_PORT == 9092
        assert settings.ZOOKEEPER_PORT == 2181
        
    def test_timeout_configuration(self):
        """Test timeout configuration defaults"""
        from autocoder_cc.core.config import Settings
        
        settings = Settings(ENVIRONMENT='development')
        assert settings.RETRY_TIMEOUT_MULTIPLIER == 1.5
        assert settings.MAX_RETRY_TIMEOUT == 300
        assert settings.HEALTH_CHECK_TIMEOUT == 5
        assert settings.COMPONENT_GENERATION_TIMEOUT == 60
        
    def test_environment_variable_override(self):
        """Test environment variables override defaults"""
        os.environ['JWT_SECRET_KEY'] = 'test-jwt-key'
        os.environ['KAFKA_BROKERS'] = 'test-broker:9092'
        
        from autocoder_cc.core.config import Settings
        settings = Settings()
        
        assert settings.JWT_SECRET_KEY == 'test-jwt-key'
        assert settings.KAFKA_BROKERS == 'test-broker:9092'
        
        # Cleanup
        del os.environ['JWT_SECRET_KEY']
        del os.environ['KAFKA_BROKERS']
        
    def test_llm_configuration(self):
        """Test LLM provider configuration"""
        from autocoder_cc.core.config import Settings
        
        settings = Settings()
        
        # Should have model names configured
        assert settings.OPENAI_MODEL == 'o3'
        assert settings.GEMINI_MODEL == 'gemini-2.5-flash'
        assert settings.ANTHROPIC_MODEL == 'claude-sonnet-4-20250514'
        
    def test_validation_settings(self):
        """Test validation configuration"""
        from autocoder_cc.core.config import Settings
        
        settings = Settings()
        
        assert settings.ENABLE_SEMANTIC_VALIDATION == True
        assert settings.ENABLE_INTEGRATION_VALIDATION == True
        assert settings.VALIDATION_TIMEOUT == 30
        assert settings.VALIDATION_STRICT_MODE == True
        
    def test_get_retry_timeout(self):
        """Test progressive retry timeout calculation"""
        from autocoder_cc.core.config import Settings
        
        settings = Settings(ENVIRONMENT='development')
        
        # Test exponential backoff
        assert settings.get_retry_timeout(0) == 60  # Base timeout
        assert settings.get_retry_timeout(1) == 90  # 60 * 1.5
        assert settings.get_retry_timeout(2) == 135  # 60 * 1.5^2
        
        # Test max cap
        assert settings.get_retry_timeout(10) <= 300  # Should be capped at MAX_RETRY_TIMEOUT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])