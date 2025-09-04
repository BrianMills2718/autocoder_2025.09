"""
Unit tests for the prompt management system.

These tests verify:
1. Prompt loading and caching
2. Variable validation
3. Template rendering
4. Error handling
"""

import pytest
from pathlib import Path
import tempfile
import yaml
from autocoder_cc.prompts import PromptManager, PromptError
from autocoder_cc.prompts.prompt_manager import (
    PromptNotFoundError, 
    PromptValidationError,
    LoadedPrompt,
    PromptMetadata,
    PromptVariable
)


class TestPromptManager:
    """Test the prompt manager functionality."""
    
    @pytest.fixture
    def temp_prompts_dir(self):
        """Create a temporary directory with test prompts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            prompts_dir = Path(tmpdir)
            
            # Create directory structure
            (prompts_dir / "component_generation").mkdir(parents=True)
            (prompts_dir / "blueprint_generation").mkdir(parents=True)
            
            # Create test prompt files
            self._create_test_prompts(prompts_dir)
            
            yield prompts_dir
    
    def _create_test_prompts(self, prompts_dir: Path):
        """Create test prompt files."""
        # Simple component prompt
        simple_prompt = {
            "metadata": {
                "version": "1.0.0",
                "description": "Test component prompt",
                "author": "test"
            },
            "variables": [
                {"name": "component_name", "description": "Component name"},
                {"name": "component_type", "description": "Component type"}
            ],
            "prompt": "Generate {{ component_type }} component named {{ component_name }}",
            "examples": [
                {
                    "input": {
                        "component_name": "TestStore",
                        "component_type": "Store"
                    },
                    "output": "class TestStore(Store): pass"
                }
            ]
        }
        
        with open(prompts_dir / "component_generation" / "simple.yaml", "w") as f:
            yaml.dump(simple_prompt, f)
        
        # Complex prompt with optional variables
        complex_prompt = {
            "metadata": {
                "version": "2.0.0",
                "description": "Complex prompt with optional vars",
                "author": "test",
                "tags": ["component", "advanced"]
            },
            "variables": [
                {"name": "name", "description": "Name", "required": True},
                {"name": "config", "description": "Configuration", "required": True},
                {"name": "debug", "description": "Debug mode", "required": False, "default": False},
                {"name": "timeout", "description": "Timeout", "required": False, "default": 30}
            ],
            "prompt": """
Component: {{ name }}
Config: {{ config | tojson }}
Debug: {{ debug }}
Timeout: {{ timeout }}s
""",
            "examples": []
        }
        
        with open(prompts_dir / "component_generation" / "complex.yaml", "w") as f:
            yaml.dump(complex_prompt, f)
        
        # Invalid prompt (missing required fields)
        invalid_prompt = {
            "metadata": {"version": "1.0.0"},
            # Missing 'prompt' field
        }
        
        with open(prompts_dir / "blueprint_generation" / "invalid.yaml", "w") as f:
            yaml.dump(invalid_prompt, f)
    
    def test_load_simple_prompt(self, temp_prompts_dir):
        """Test loading a simple prompt file."""
        manager = PromptManager(temp_prompts_dir)
        
        # Load prompt
        prompt = manager.load_prompt("component_generation/simple.yaml")
        
        # Verify loaded data
        assert isinstance(prompt, LoadedPrompt)
        assert prompt.metadata.version == "1.0.0"
        assert prompt.metadata.description == "Test component prompt"
        assert len(prompt.variables) == 2
        assert prompt.variables[0].name == "component_name"
        assert prompt.variables[1].name == "component_type"
        assert "Generate" in prompt.template
        assert len(prompt.examples) == 1
    
    def test_prompt_caching(self, temp_prompts_dir):
        """Test that prompts are cached after first load."""
        manager = PromptManager(temp_prompts_dir)
        
        # Load prompt twice
        prompt1 = manager.load_prompt("component_generation/simple.yaml")
        prompt2 = manager.load_prompt("component_generation/simple.yaml")
        
        # Should be the same object (cached)
        assert prompt1 is prompt2
    
    def test_load_nonexistent_prompt(self, temp_prompts_dir):
        """Test loading a prompt that doesn't exist."""
        manager = PromptManager(temp_prompts_dir)
        
        with pytest.raises(PromptNotFoundError, match="not found"):
            manager.load_prompt("nonexistent/prompt.yaml")
    
    def test_load_invalid_prompt(self, temp_prompts_dir):
        """Test loading an invalid prompt file."""
        manager = PromptManager(temp_prompts_dir)
        
        with pytest.raises(PromptValidationError, match="Missing 'prompt'"):
            manager.load_prompt("blueprint_generation/invalid.yaml")
    
    def test_render_simple_prompt(self, temp_prompts_dir):
        """Test rendering a simple prompt."""
        manager = PromptManager(temp_prompts_dir)
        
        # Render with all required variables
        rendered = manager.render_prompt(
            "component_generation/simple.yaml",
            {
                "component_name": "UserStore",
                "component_type": "Store"
            }
        )
        
        assert "Generate Store component named UserStore" in rendered
    
    def test_render_missing_required_variable(self, temp_prompts_dir):
        """Test rendering with missing required variables."""
        manager = PromptManager(temp_prompts_dir)
        
        with pytest.raises(PromptValidationError, match="Missing required variables"):
            manager.render_prompt(
                "component_generation/simple.yaml",
                {"component_name": "UserStore"}  # Missing component_type
            )
    
    def test_render_with_optional_variables(self, temp_prompts_dir):
        """Test rendering with optional variables and defaults."""
        manager = PromptManager(temp_prompts_dir)
        
        # Render without optional variables (should use defaults)
        rendered = manager.render_prompt(
            "component_generation/complex.yaml",
            {
                "name": "TestComponent",
                "config": {"key": "value"}
            }
        )
        
        assert "Component: TestComponent" in rendered
        assert "Debug: False" in rendered  # Default value
        assert "Timeout: 30s" in rendered  # Default value
        
        # Render with optional variables provided
        rendered = manager.render_prompt(
            "component_generation/complex.yaml",
            {
                "name": "TestComponent",
                "config": {"key": "value"},
                "debug": True,
                "timeout": 60
            }
        )
        
        assert "Debug: True" in rendered
        assert "Timeout: 60s" in rendered
    
    def test_list_prompts(self, temp_prompts_dir):
        """Test listing available prompts."""
        manager = PromptManager(temp_prompts_dir)
        
        # List all prompts
        all_prompts = manager.list_prompts()
        assert len(all_prompts) >= 3
        assert "component_generation/simple.yaml" in all_prompts
        assert "component_generation/complex.yaml" in all_prompts
        
        # List prompts in specific category
        component_prompts = manager.list_prompts("component_generation")
        assert len(component_prompts) >= 2
        assert all("component_generation" in p for p in component_prompts)
    
    def test_get_prompt_info(self, temp_prompts_dir):
        """Test getting prompt information."""
        manager = PromptManager(temp_prompts_dir)
        
        info = manager.get_prompt_info("component_generation/complex.yaml")
        
        assert info["path"] == "component_generation/complex.yaml"
        assert info["metadata"]["version"] == "2.0.0"
        assert info["metadata"]["tags"] == ["component", "advanced"]
        assert len(info["variables"]) == 4
        
        # Check variable info
        var_names = [v["name"] for v in info["variables"]]
        assert "name" in var_names
        assert "debug" in var_names
        
        # Check optional variable has default
        debug_var = next(v for v in info["variables"] if v["name"] == "debug")
        assert debug_var["required"] is False
        assert debug_var["default"] is False
    
    def test_validate_prompt_file(self, temp_prompts_dir):
        """Test prompt file validation."""
        manager = PromptManager(temp_prompts_dir)
        
        # Valid prompt should have no issues
        issues = manager.validate_prompt_file("component_generation/simple.yaml")
        assert len(issues) == 0
        
        # Create prompt with issues
        problematic_prompt = {
            "metadata": {"version": "1.0.0"},  # Missing description
            "variables": ["var1"],
            "prompt": "Test {var1} {var2}",  # var2 not defined
            # No examples
        }
        
        with open(temp_prompts_dir / "test_problematic.yaml", "w") as f:
            yaml.dump(problematic_prompt, f)
        
        issues = manager.validate_prompt_file("test_problematic.yaml")
        assert "Missing description" in str(issues)
        assert "No examples" in str(issues)
    
    def test_complex_template_rendering(self, temp_prompts_dir):
        """Test rendering complex templates with loops and conditions."""
        # Create a complex prompt
        complex_prompt = {
            "metadata": {
                "version": "1.0.0",
                "description": "Complex template test"
            },
            "variables": ["components", "include_tests"],
            "prompt": """
System Components:
{% for comp in components %}
- {{ comp.name }} ({{ comp.type }})
  {% if comp.config %}
  Config:
    {% for key, value in comp.config.items() %}
    {{ key }}: {{ value }}
    {% endfor %}
  {% endif %}
{% endfor %}

{% if include_tests %}
Generate tests for all components.
{% endif %}
"""
        }
        
        with open(temp_prompts_dir / "complex_template.yaml", "w") as f:
            yaml.dump(complex_prompt, f)
        
        manager = PromptManager(temp_prompts_dir)
        
        rendered = manager.render_prompt(
            "complex_template.yaml",
            {
                "components": [
                    {"name": "UserStore", "type": "Store", "config": {"db": "postgres"}},
                    {"name": "UserAPI", "type": "APIEndpoint", "config": None}
                ],
                "include_tests": True
            }
        )
        
        assert "UserStore (Store)" in rendered
        assert "db: postgres" in rendered
        assert "UserAPI (APIEndpoint)" in rendered
        assert "Generate tests for all components." in rendered
    
    def test_clear_cache(self, temp_prompts_dir):
        """Test clearing the prompt cache."""
        manager = PromptManager(temp_prompts_dir)
        
        # Load a prompt to populate cache
        prompt1 = manager.load_prompt("component_generation/simple.yaml")
        assert len(manager._cache) > 0
        
        # Clear cache
        manager.clear_cache()
        assert len(manager._cache) == 0
        
        # Load again - should be a new object
        prompt2 = manager.load_prompt("component_generation/simple.yaml")
        assert prompt1 is not prompt2  # Different objects since cache was cleared
    
    def test_jinja_undefined_variable_error(self, temp_prompts_dir):
        """Test that undefined variables in templates raise errors."""
        undefined_prompt = {
            "metadata": {"version": "1.0.0", "description": "Test"},
            "variables": ["defined_var"],
            "prompt": "{{ defined_var }} and {{ undefined_var }}"
        }
        
        with open(temp_prompts_dir / "undefined_test.yaml", "w") as f:
            yaml.dump(undefined_prompt, f)
        
        manager = PromptManager(temp_prompts_dir)
        
        with pytest.raises(PromptValidationError, match="Undefined variable"):
            manager.render_prompt(
                "undefined_test.yaml",
                {"defined_var": "test"}
            )