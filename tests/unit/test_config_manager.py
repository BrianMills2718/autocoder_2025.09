"""
Test-Driven Development for Configuration Manager
RED Phase: Write failing tests first
"""
import pytest
import ast
from unittest.mock import Mock, patch

# This will fail initially as we haven't implemented ConfigurationAnalyzer yet
from autocoder_cc.generation.deployment.config_manager import ConfigurationAnalyzer
from autocoder_cc.generation.deployment.environment_templates import EnvironmentTemplateManager


class TestConfigurationAnalyzer:
    """Test suite for ConfigurationAnalyzer - RED phase"""
    
    def test_analyze_component_requirements_extracts_db_config(self):
        """Test that analyzer extracts database configuration requirements"""
        analyzer = ConfigurationAnalyzer()
        component_code = """
class TaskService:
    def __init__(self, config):
        self.db_connection_string = config.get('db_connection_string')
        self.database = Database(self.db_connection_string)
"""
        requirements = analyzer.analyze_component_requirements(component_code)
        assert "db_connection_string" in requirements
        assert requirements["db_connection_string"]["required"] is True
        
    def test_analyze_component_requirements_extracts_multiple_configs(self):
        """Test that analyzer extracts multiple configuration requirements"""
        analyzer = ConfigurationAnalyzer()
        component_code = """
class WebService:
    def __init__(self, config):
        self.api_key = config.get('api_key')
        self.port = config.get('port', 8080)
        self.debug = config.get('debug', False)
"""
        requirements = analyzer.analyze_component_requirements(component_code)
        assert "api_key" in requirements
        assert "port" in requirements
        assert "debug" in requirements
        assert requirements["api_key"]["required"] is True
        assert requirements["port"]["required"] is False
        assert requirements["port"]["default"] == 8080
        
    def test_analyze_component_requirements_handles_empty_code(self):
        """Test that analyzer handles empty component code gracefully"""
        analyzer = ConfigurationAnalyzer()
        requirements = analyzer.analyze_component_requirements("")
        assert requirements == {}
        
    def test_analyze_component_requirements_handles_invalid_syntax(self):
        """Test that analyzer handles invalid Python syntax"""
        analyzer = ConfigurationAnalyzer()
        with pytest.raises(SyntaxError):
            analyzer.analyze_component_requirements("invalid python code {{{")
            
    @pytest.mark.asyncio
    async def test_generate_environment_config_creates_test_config(self):
        """Test that environment config generator creates test configuration"""
        template_manager = EnvironmentTemplateManager()
        requirements = {
            "db_connection_string": {"required": True, "type": "string"},
            "port": {"required": False, "default": 8080, "type": "int"}
        }
        config = template_manager.resolve_template("test", requirements)
        assert "db_connection_string" in config
        assert config["db_connection_string"] == "sqlite:///test.db"
        assert config["port"] == 8080
        
    @pytest.mark.asyncio
    async def test_generate_environment_config_creates_dev_config(self):
        """Test that environment config generator creates development configuration"""
        template_manager = EnvironmentTemplateManager()
        requirements = {
            "db_connection_string": {"required": True, "type": "string"}
        }
        config = template_manager.resolve_template("dev", requirements)
        assert config["db_connection_string"] == "postgresql://localhost:5432/dev_db"
        
    @pytest.mark.asyncio
    async def test_generate_environment_config_creates_prod_config(self):
        """Test that environment config generator creates production configuration"""
        template_manager = EnvironmentTemplateManager()
        requirements = {
            "db_connection_string": {"required": True, "type": "string"},
            "secret_key": {"required": True, "type": "string"}
        }
        config = template_manager.resolve_template("prod", requirements)
        # Production should use environment variables
        assert "${DB_CONNECTION_STRING}" in config["db_connection_string"]
        assert "${SECRET_KEY}" in config["secret_key"]