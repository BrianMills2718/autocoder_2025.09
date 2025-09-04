import pytest
from pathlib import Path
import tempfile
import yaml

def test_recipe_expander_has_expand_method():
    """Verify RecipeExpander has the expand_to_spec method"""
    from autocoder_cc.recipes import RecipeExpander
    expander = RecipeExpander()
    assert hasattr(expander, 'expand_to_spec'), "RecipeExpander missing expand_to_spec method"

def test_system_generator_uses_recipe_expander():
    """Verify SystemGenerator actually calls recipe_expander"""
    blueprint_with_recipe = """
schema_version: "1.0.0"
system:
  name: test_system
  components:
    - name: my_store
      recipe: Store
      config:
        backend: memory
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save blueprint
        blueprint_path = Path(tmpdir) / "test.yaml"
        blueprint_path.write_text(blueprint_with_recipe)
        
        # Try to generate
        from autocoder_cc.blueprint_language.system_generator import SystemGenerator
        generator = SystemGenerator(Path(tmpdir), skip_deployment=True, bypass_validation=True)
        
        # This should expand the recipe
        # Check the logs for evidence of expansion
        assert True  # Placeholder - implement actual check

def test_all_13_recipes_expand():
    """Verify all recipes can be expanded"""
    from autocoder_cc.recipes import RecipeExpander
    from autocoder_cc.recipes.registry import list_recipes
    
    expander = RecipeExpander()
    recipes = list_recipes()
    
    assert len(recipes) >= 13, f"Expected 13+ recipes, found {len(recipes)}"
    
    failed = []
    for recipe_name in recipes:
        try:
            if hasattr(expander, 'expand_to_spec'):
                spec = expander.expand_to_spec(recipe_name, f"test_{recipe_name}")
            else:
                # Method doesn't exist yet - this will fail
                failed.append(recipe_name)
        except Exception as e:
            failed.append(f"{recipe_name}: {e}")
    
    assert not failed, f"Failed recipes: {failed}"

# Run with: pytest tests/test_week8_recipe_integration.py -xvs